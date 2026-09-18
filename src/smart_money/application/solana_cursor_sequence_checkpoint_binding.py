from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_store import (
    JsonSolanaCursorSequenceCheckpointStore,
)
from smart_money.adapters.persistence.solana_observation_sequence_store import (
    JsonSolanaObservationSequenceStore,
)
from smart_money.adapters.persistence.solana_slot_cursor_store import JsonSolanaSlotCursorStore
from smart_money.core.ids import deterministic_id
from smart_money.domain.solana_observation import (
    SolanaChainObservation,
    SolanaCursorSequenceCheckpoint,
    replay_solana_observation_order,
)


@dataclass(frozen=True, slots=True)
class SolanaCursorSequenceCheckpointBindingReceipt:
    receipt_id: str
    previous_cursor_id: str
    current_cursor_id: str
    sequence_id: str
    checkpoint_id: str
    observation_id: str
    schema_version: str = "solana_cursor_sequence_checkpoint_binding.v1"

    def __post_init__(self) -> None:
        for name in (
            "receipt_id", "previous_cursor_id", "current_cursor_id",
            "sequence_id", "checkpoint_id", "observation_id",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.schema_version != "solana_cursor_sequence_checkpoint_binding.v1":
            raise ValueError("unsupported Solana checkpoint binding schema_version")
        expected = deterministic_id(
            "solana_cursor_sequence_checkpoint_binding",
            self.identity_payload(),
        )
        if self.receipt_id != expected:
            raise ValueError("receipt_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "current_cursor_id": self.current_cursor_id,
            "observation_id": self.observation_id,
            "previous_cursor_id": self.previous_cursor_id,
            "schema_version": self.schema_version,
            "sequence_id": self.sequence_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}


@dataclass(frozen=True, slots=True)
class SolanaCursorSequenceCheckpointBindingReplayReceipt:
    replay_id: str
    original_receipt_id: str
    matches: bool
    schema_version: str = "solana_cursor_sequence_checkpoint_binding_replay.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.original_receipt_id, str) or not self.original_receipt_id.strip():
            raise ValueError("original_receipt_id must be a non-empty string")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be a boolean")
        if self.schema_version != "solana_cursor_sequence_checkpoint_binding_replay.v1":
            raise ValueError("unsupported Solana checkpoint binding replay schema_version")
        expected = deterministic_id(
            "solana_cursor_sequence_checkpoint_binding_replay",
            {
                "original_receipt_id": self.original_receipt_id,
                "schema_version": self.schema_version,
            },
        )
        if self.replay_id != expected:
            raise ValueError("replay_id does not match deterministic payload")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "matches": self.matches,
            "original_receipt_id": self.original_receipt_id,
            "replay_id": self.replay_id,
            "schema_version": self.schema_version,
        }


def verify_solana_cursor_sequence_checkpoint_binding_replay(
    cursor_store: JsonSolanaSlotCursorStore,
    sequence_store: JsonSolanaObservationSequenceStore,
    checkpoint_store: JsonSolanaCursorSequenceCheckpointStore,
    observations: tuple[SolanaChainObservation, ...],
    receipt: SolanaCursorSequenceCheckpointBindingReceipt,
) -> SolanaCursorSequenceCheckpointBindingReplayReceipt:
    if not isinstance(receipt, SolanaCursorSequenceCheckpointBindingReceipt):
        raise TypeError("receipt must be a SolanaCursorSequenceCheckpointBindingReceipt")
    if not isinstance(observations, tuple) or not observations:
        raise ValueError("observations must be a non-empty tuple")
    sequence = replay_solana_observation_order(observations)
    cursor = cursor_store.load()
    checkpoint = checkpoint_store.load()
    if checkpoint is None:
        raise ValueError("persisted Solana checkpoint is missing")
    if sequence_store.get(sequence.sequence_id) != sequence:
        raise ValueError("persisted Solana sequence does not match replay")
    if checkpoint.sequence_id != sequence.sequence_id or checkpoint.cursor != cursor:
        raise ValueError("persisted Solana checkpoint does not match replay")
    replayed = SolanaCursorSequenceCheckpointBindingReceipt(
        receipt_id=receipt.receipt_id,
        previous_cursor_id=receipt.previous_cursor_id,
        current_cursor_id=cursor.canonical_id,
        sequence_id=sequence.sequence_id,
        checkpoint_id=checkpoint.checkpoint_id,
        observation_id=observations[-1].observation_id,
    )
    if replayed != receipt:
        raise ValueError("Solana checkpoint binding receipt does not match replay")
    return SolanaCursorSequenceCheckpointBindingReplayReceipt(
        replay_id=deterministic_id(
            "solana_cursor_sequence_checkpoint_binding_replay",
            {
                "original_receipt_id": receipt.receipt_id,
                "schema_version": "solana_cursor_sequence_checkpoint_binding_replay.v1",
            },
        ),
        original_receipt_id=receipt.receipt_id,
        matches=True,
    )


def advance_and_checkpoint_solana_cursor(
    cursor_store: JsonSolanaSlotCursorStore,
    sequence_store: JsonSolanaObservationSequenceStore,
    checkpoint_store: JsonSolanaCursorSequenceCheckpointStore,
    observations: tuple[SolanaChainObservation, ...],
) -> SolanaCursorSequenceCheckpointBindingReceipt:
    if not isinstance(cursor_store, JsonSolanaSlotCursorStore):
        raise TypeError("cursor_store must be a JsonSolanaSlotCursorStore")
    if not isinstance(sequence_store, JsonSolanaObservationSequenceStore):
        raise TypeError("sequence_store must be a JsonSolanaObservationSequenceStore")
    if not isinstance(checkpoint_store, JsonSolanaCursorSequenceCheckpointStore):
        raise TypeError("checkpoint_store must be a JsonSolanaCursorSequenceCheckpointStore")
    if not isinstance(observations, tuple) or not observations:
        raise ValueError("observations must be a non-empty tuple")
    if not all(isinstance(item, SolanaChainObservation) for item in observations):
        raise TypeError("observations must contain SolanaChainObservation values")
    previous = cursor_store.load()
    current = previous.advance(observations[-1])
    sequence = replay_solana_observation_order(observations)
    sequence_store.append(sequence)
    cursor_store.save(current)
    checkpoint = SolanaCursorSequenceCheckpoint.from_sequence(sequence, current)
    checkpoint_store.save(checkpoint)
    if cursor_store.load() != current or checkpoint_store.load() != checkpoint:
        raise ValueError("persisted Solana cursor checkpoint binding does not match")
    identity = {
        "checkpoint_id": checkpoint.checkpoint_id,
        "current_cursor_id": current.canonical_id,
        "observation_id": observations[-1].observation_id,
        "previous_cursor_id": previous.canonical_id,
        "schema_version": "solana_cursor_sequence_checkpoint_binding.v1",
        "sequence_id": sequence.sequence_id,
    }
    return SolanaCursorSequenceCheckpointBindingReceipt(
        receipt_id=deterministic_id("solana_cursor_sequence_checkpoint_binding", identity),
        previous_cursor_id=previous.canonical_id,
        current_cursor_id=current.canonical_id,
        sequence_id=sequence.sequence_id,
        checkpoint_id=checkpoint.checkpoint_id,
        observation_id=observations[-1].observation_id,
    )


__all__ = [
    "SolanaCursorSequenceCheckpointBindingReceipt",
    "SolanaCursorSequenceCheckpointBindingReplayReceipt",
    "advance_and_checkpoint_solana_cursor",
    "verify_solana_cursor_sequence_checkpoint_binding_replay",
]
