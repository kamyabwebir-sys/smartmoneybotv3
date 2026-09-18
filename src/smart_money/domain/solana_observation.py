from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from smart_money.core.ids import deterministic_id
from smart_money.domain.market_identity import ChainId

_SCHEMA_VERSION = "solana_chain_observation.v1"


class SolanaCommitment(str, Enum):
    PROCESSED = "processed"
    CONFIRMED = "confirmed"
    FINALIZED = "finalized"


_COMMITMENT_RANK = {
    SolanaCommitment.PROCESSED: 0,
    SolanaCommitment.CONFIRMED: 1,
    SolanaCommitment.FINALIZED: 2,
}


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key.strip(): _freeze(value[key]) for key in sorted(value)}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if value is None or isinstance(value, str | int | bool):
        return value
    raise TypeError(f"unsupported observation fact type: {type(value).__name__}")


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain(value[key]) for key in sorted(value)}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class SolanaChainObservation:
    """Immutable point-in-time Solana observation; not a transaction command."""

    slot: int
    observed_at: int
    transaction_signature: str
    program_id: str
    subject: str
    facts: Mapping[str, Any] = field(default_factory=dict)
    commitment: str = "finalized"
    chain: ChainId = field(
        default_factory=lambda: ChainId("solana", "mainnet-beta")
    )
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "transaction_signature",
            "program_id",
            "subject",
            "commitment",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
            object.__setattr__(self, name, value.strip())
        for name in ("slot", "observed_at"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if not isinstance(self.chain, ChainId):
            raise TypeError("chain must be a ChainId")
        if self.chain != ChainId("solana", "mainnet-beta"):
            raise ValueError("C1.1 observations require Solana mainnet-beta")
        if not isinstance(self.facts, Mapping):
            raise TypeError("facts must be a mapping")
        if self.commitment not in {item.value for item in SolanaCommitment}:
            raise ValueError("unsupported Solana commitment")
        object.__setattr__(self, "facts", _freeze(self.facts))
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported Solana observation schema_version")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "chain": self.chain.canonical_dict(),
            "commitment": self.commitment,
            "facts": _plain(self.facts),
            "observed_at": self.observed_at,
            "program_id": self.program_id,
            "schema_version": self.schema_version,
            "slot": self.slot,
            "subject": self.subject,
            "transaction_signature": self.transaction_signature,
        }

    @property
    def observation_id(self) -> str:
        return deterministic_id("solana_chain_observation", self.canonical_dict())

    @property
    def ordering_key(self) -> tuple[int, int, str]:
        return self.slot, self.observed_at, self.transaction_signature


@dataclass(frozen=True, slots=True)
class SolanaSlotCursor:
    slot: int = 0
    observed_at: int = 0
    transaction_signature: str = ""
    schema_version: str = "solana_slot_cursor.v1"

    def __post_init__(self) -> None:
        for name in ("slot", "observed_at"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if not isinstance(self.transaction_signature, str):
            raise TypeError("transaction_signature must be a string")
        if self.slot == 0 and self.observed_at == 0 and self.transaction_signature:
            raise ValueError("empty cursor cannot contain a transaction signature")
        if self.slot > 0 and not self.transaction_signature.strip():
            raise ValueError("advanced cursor requires a transaction signature")
        if self.schema_version != "solana_slot_cursor.v1":
            raise ValueError("unsupported Solana slot cursor schema_version")

    @classmethod
    def from_observation(cls, observation: SolanaChainObservation) -> SolanaSlotCursor:
        if not isinstance(observation, SolanaChainObservation):
            raise TypeError("observation must be a SolanaChainObservation")
        return cls(
            slot=observation.slot,
            observed_at=observation.observed_at,
            transaction_signature=observation.transaction_signature,
        )

    @property
    def ordering_key(self) -> tuple[int, int, str]:
        return self.slot, self.observed_at, self.transaction_signature

    @property
    def canonical_id(self) -> str:
        return deterministic_id("solana_slot_cursor", self.canonical_dict())

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "observed_at": self.observed_at,
            "schema_version": self.schema_version,
            "slot": self.slot,
            "transaction_signature": self.transaction_signature,
        }

    def advance(self, observation: SolanaChainObservation) -> SolanaSlotCursor:
        candidate = SolanaSlotCursor.from_observation(observation)
        if candidate.ordering_key < self.ordering_key:
            raise ValueError("Solana slot cursor cannot regress")
        if (
            candidate.ordering_key == self.ordering_key
            and candidate != self
            and self.slot != 0
        ):
            raise ValueError("Solana slot cursor ordering collision")
        return candidate


def validate_solana_observation_order(
    previous: SolanaChainObservation,
    current: SolanaChainObservation,
) -> None:
    if not isinstance(previous, SolanaChainObservation) or not isinstance(
        current, SolanaChainObservation
    ):
        raise TypeError("observations must be SolanaChainObservation values")
    if current.ordering_key < previous.ordering_key:
        raise ValueError("Solana observation ordering regressed")
    if (
        current.ordering_key == previous.ordering_key
        and current.observation_id != previous.observation_id
    ):
        raise ValueError("Solana observation ordering collision")


def validate_solana_commitment_transition(
    previous: SolanaChainObservation,
    current: SolanaChainObservation,
) -> None:
    """Allow only monotonic commitment upgrades for the same observation."""
    if not isinstance(previous, SolanaChainObservation) or not isinstance(
        current, SolanaChainObservation
    ):
        raise TypeError("observations must be SolanaChainObservation values")
    if previous.observation_id != current.observation_id and (
        previous.slot != current.slot
        or previous.transaction_signature != current.transaction_signature
    ):
        raise ValueError("commitment transition requires the same observation")
    old = SolanaCommitment(previous.commitment)
    new = SolanaCommitment(current.commitment)
    if _COMMITMENT_RANK[new] < _COMMITMENT_RANK[old]:
        raise ValueError("Solana commitment transition regressed")


@dataclass(frozen=True, slots=True)
class SolanaCommitmentReplayReceipt:
    previous_observation_id: str
    current_observation_id: str
    previous_commitment: str
    current_commitment: str
    transition_id: str
    schema_version: str = "solana_commitment_replay.v1"

    def __post_init__(self) -> None:
        for name in (
            "previous_observation_id",
            "current_observation_id",
            "previous_commitment",
            "current_commitment",
            "transition_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.schema_version != "solana_commitment_replay.v1":
            raise ValueError("unsupported Solana commitment replay schema_version")
        expected = deterministic_id(
            "solana_commitment_replay",
            {
                "current_commitment": self.current_commitment,
                "current_observation_id": self.current_observation_id,
                "previous_commitment": self.previous_commitment,
                "previous_observation_id": self.previous_observation_id,
                "schema_version": self.schema_version,
            },
        )
        if self.transition_id != expected:
            raise ValueError("transition_id does not match deterministic payload")

    def canonical_dict(self) -> dict[str, str]:
        return {
            "current_commitment": self.current_commitment,
            "current_observation_id": self.current_observation_id,
            "previous_commitment": self.previous_commitment,
            "previous_observation_id": self.previous_observation_id,
            "schema_version": self.schema_version,
            "transition_id": self.transition_id,
        }


def replay_solana_commitment_transition(
    previous: SolanaChainObservation,
    current: SolanaChainObservation,
) -> SolanaCommitmentReplayReceipt:
    validate_solana_commitment_transition(previous, current)
    identity = {
        "current_commitment": current.commitment,
        "current_observation_id": current.observation_id,
        "previous_commitment": previous.commitment,
        "previous_observation_id": previous.observation_id,
        "schema_version": "solana_commitment_replay.v1",
    }
    return SolanaCommitmentReplayReceipt(
        previous_observation_id=previous.observation_id,
        current_observation_id=current.observation_id,
        previous_commitment=previous.commitment,
        current_commitment=current.commitment,
        transition_id=deterministic_id("solana_commitment_replay", identity),
    )


@dataclass(frozen=True, slots=True)
class SolanaOrderingReplayReceipt:
    observation_ids: tuple[str, ...]
    first_ordering_key: tuple[int, int, str]
    last_ordering_key: tuple[int, int, str]
    sequence_id: str
    schema_version: str = "solana_ordering_replay.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.observation_ids, tuple) or not self.observation_ids:
            raise ValueError("observation_ids must be a non-empty tuple")
        if not all(isinstance(item, str) and item.strip() for item in self.observation_ids):
            raise ValueError("observation_ids must contain non-empty text")
        for name in ("first_ordering_key", "last_ordering_key"):
            key = getattr(self, name)
            if (
                not isinstance(key, tuple)
                or len(key) != 3
                or isinstance(key[0], bool)
                or not isinstance(key[0], int)
                or isinstance(key[1], bool)
                or not isinstance(key[1], int)
                or not isinstance(key[2], str)
            ):
                raise TypeError(f"{name} must be a valid ordering key")
        if self.schema_version != "solana_ordering_replay.v1":
            raise ValueError("unsupported Solana ordering replay schema_version")
        expected = deterministic_id(
            "solana_ordering_replay",
            {
                "first_ordering_key": self.first_ordering_key,
                "last_ordering_key": self.last_ordering_key,
                "observation_ids": self.observation_ids,
                "schema_version": self.schema_version,
            },
        )
        if self.sequence_id != expected:
            raise ValueError("sequence_id does not match deterministic payload")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "first_ordering_key": self.first_ordering_key,
            "last_ordering_key": self.last_ordering_key,
            "observation_ids": self.observation_ids,
            "schema_version": self.schema_version,
            "sequence_id": self.sequence_id,
        }


@dataclass(frozen=True, slots=True)
class SolanaCursorSequenceCheckpoint:
    """Immutable binding between a cursor and the tail of an ordered sequence."""

    cursor: SolanaSlotCursor
    sequence_id: str
    observation_count: int
    last_observation_id: str
    last_ordering_key: tuple[int, int, str]
    checkpoint_id: str
    schema_version: str = "solana_cursor_sequence_checkpoint.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.cursor, SolanaSlotCursor):
            raise TypeError("cursor must be a SolanaSlotCursor")
        for name in ("sequence_id", "last_observation_id", "checkpoint_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if isinstance(self.observation_count, bool) or not isinstance(
            self.observation_count, int
        ):
            raise TypeError("observation_count must be an integer")
        if self.observation_count < 1:
            raise ValueError("observation_count must be positive")
        key = self.last_ordering_key
        if (
            not isinstance(key, tuple)
            or len(key) != 3
            or isinstance(key[0], bool)
            or not isinstance(key[0], int)
            or isinstance(key[1], bool)
            or not isinstance(key[1], int)
            or not isinstance(key[2], str)
            or not key[2].strip()
        ):
            raise TypeError("last_ordering_key must be a valid ordering key")
        if self.cursor.ordering_key != key:
            raise ValueError("cursor does not match checkpoint last_ordering_key")
        if self.schema_version != "solana_cursor_sequence_checkpoint.v1":
            raise ValueError("unsupported Solana cursor sequence checkpoint schema_version")
        expected = deterministic_id(
            "solana_cursor_sequence_checkpoint",
            {
                "cursor": self.cursor.canonical_dict(),
                "last_observation_id": self.last_observation_id.strip(),
                "last_ordering_key": self.last_ordering_key,
                "observation_count": self.observation_count,
                "schema_version": self.schema_version,
                "sequence_id": self.sequence_id.strip(),
            },
        )
        if self.checkpoint_id != expected:
            raise ValueError("checkpoint_id does not match deterministic payload")

    @classmethod
    def from_sequence(
        cls,
        sequence: SolanaOrderingReplayReceipt,
        cursor: SolanaSlotCursor,
    ) -> SolanaCursorSequenceCheckpoint:
        if not isinstance(sequence, SolanaOrderingReplayReceipt):
            raise TypeError("sequence must be a SolanaOrderingReplayReceipt")
        if not isinstance(cursor, SolanaSlotCursor):
            raise TypeError("cursor must be a SolanaSlotCursor")
        if cursor.ordering_key != sequence.last_ordering_key:
            raise ValueError("cursor does not match sequence tail")
        identity = {
            "cursor": cursor.canonical_dict(),
            "last_observation_id": sequence.observation_ids[-1],
            "last_ordering_key": sequence.last_ordering_key,
            "observation_count": len(sequence.observation_ids),
            "schema_version": "solana_cursor_sequence_checkpoint.v1",
            "sequence_id": sequence.sequence_id,
        }
        return cls(
            cursor=cursor,
            sequence_id=sequence.sequence_id,
            observation_count=len(sequence.observation_ids),
            last_observation_id=sequence.observation_ids[-1],
            last_ordering_key=sequence.last_ordering_key,
            checkpoint_id=deterministic_id(
                "solana_cursor_sequence_checkpoint", identity
            ),
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "cursor": self.cursor.canonical_dict(),
            "last_observation_id": self.last_observation_id.strip(),
            "last_ordering_key": self.last_ordering_key,
            "observation_count": self.observation_count,
            "schema_version": self.schema_version,
            "sequence_id": self.sequence_id.strip(),
        }


def replay_solana_observation_order(
    observations: Iterable[SolanaChainObservation],
) -> SolanaOrderingReplayReceipt:
    values = tuple(observations)
    if not values:
        raise ValueError("observations must be non-empty")
    if not all(isinstance(item, SolanaChainObservation) for item in values):
        raise TypeError("observations must contain SolanaChainObservation values")
    for previous, current in zip(values, values[1:]):
        validate_solana_observation_order(previous, current)
    identity = {
        "first_ordering_key": values[0].ordering_key,
        "last_ordering_key": values[-1].ordering_key,
        "observation_ids": tuple(item.observation_id for item in values),
        "schema_version": "solana_ordering_replay.v1",
    }
    return SolanaOrderingReplayReceipt(
        observation_ids=identity["observation_ids"],
        first_ordering_key=values[0].ordering_key,
        last_ordering_key=values[-1].ordering_key,
        sequence_id=deterministic_id("solana_ordering_replay", identity),
    )


__all__ = [
    "SolanaChainObservation",
    "SolanaCommitment",
    "SolanaCommitmentReplayReceipt",
    "SolanaCursorSequenceCheckpoint",
    "SolanaOrderingReplayReceipt",
    "SolanaSlotCursor",
    "replay_solana_observation_order",
    "validate_solana_commitment_transition",
    "validate_solana_observation_order",
    "replay_solana_commitment_transition",
]
