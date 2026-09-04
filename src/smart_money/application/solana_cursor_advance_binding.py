from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.adapters.persistence.solana_slot_cursor_store import (
    JsonSolanaSlotCursorStore,
)
from smart_money.core.ids import deterministic_id
from smart_money.domain.solana_observation import (
    SolanaChainObservation,
    SolanaSlotCursor,
)

_SCHEMA_VERSION = "solana_cursor_advance_binding.v1"


@dataclass(frozen=True, slots=True)
class SolanaCursorAdvanceReplayReceipt:
    receipt_id: str
    original_receipt_id: str
    matches: bool
    schema_version: str = "solana_cursor_advance_replay.v1"

    def __post_init__(self) -> None:
        for name in ("receipt_id", "original_receipt_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be a boolean")
        if self.schema_version != "solana_cursor_advance_replay.v1":
            raise ValueError("unsupported Solana cursor advance replay schema_version")
        expected = deterministic_id(
            "solana_cursor_advance_replay",
            {
                "original_receipt_id": self.original_receipt_id,
                "schema_version": self.schema_version,
            },
        )
        if self.receipt_id != expected:
            raise ValueError("receipt_id does not match deterministic payload")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "matches": self.matches,
            "original_receipt_id": self.original_receipt_id,
            "receipt_id": self.receipt_id,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class SolanaCursorAdvanceReceipt:
    receipt_id: str
    previous_cursor_id: str
    current_cursor_id: str
    observation_id: str
    advanced: bool
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "receipt_id",
            "previous_cursor_id",
            "current_cursor_id",
            "observation_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.advanced, bool):
            raise TypeError("advanced must be a boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported Solana cursor advance schema_version")
        expected = deterministic_id(
            "solana_cursor_advance",
            self.identity_payload(),
        )
        if self.receipt_id != expected:
            raise ValueError("receipt_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "advanced": self.advanced,
            "current_cursor_id": self.current_cursor_id,
            "observation_id": self.observation_id,
            "previous_cursor_id": self.previous_cursor_id,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}


def advance_and_persist_solana_cursor(
    store: JsonSolanaSlotCursorStore,
    observation: SolanaChainObservation,
) -> SolanaCursorAdvanceReceipt:
    """Advance the persisted cursor and verify the saved value immediately."""
    if not isinstance(store, JsonSolanaSlotCursorStore):
        raise TypeError("store must be a JsonSolanaSlotCursorStore")
    if not isinstance(observation, SolanaChainObservation):
        raise TypeError("observation must be a SolanaChainObservation")
    previous = store.load()
    if not isinstance(previous, SolanaSlotCursor):
        raise ValueError("store returned an invalid Solana slot cursor")
    current = previous.advance(observation)
    advanced = current != previous
    store.save(current)
    persisted = store.load()
    if persisted != current:
        raise ValueError("persisted Solana slot cursor does not match advance")
    identity = {
        "advanced": advanced,
        "current_cursor_id": current.canonical_id,
        "observation_id": observation.observation_id,
        "previous_cursor_id": previous.canonical_id,
        "schema_version": _SCHEMA_VERSION,
    }
    return SolanaCursorAdvanceReceipt(
        receipt_id=deterministic_id("solana_cursor_advance", identity),
        previous_cursor_id=previous.canonical_id,
        current_cursor_id=current.canonical_id,
        observation_id=observation.observation_id,
        advanced=advanced,
    )


def verify_solana_cursor_advance_replay(
    store: JsonSolanaSlotCursorStore,
    observation: SolanaChainObservation,
    receipt: SolanaCursorAdvanceReceipt,
) -> SolanaCursorAdvanceReplayReceipt:
    if not isinstance(store, JsonSolanaSlotCursorStore):
        raise TypeError("store must be a JsonSolanaSlotCursorStore")
    if not isinstance(observation, SolanaChainObservation):
        raise TypeError("observation must be a SolanaChainObservation")
    if not isinstance(receipt, SolanaCursorAdvanceReceipt):
        raise TypeError("receipt must be a SolanaCursorAdvanceReceipt")
    current = store.load()
    if current.canonical_id != receipt.current_cursor_id:
        raise ValueError("persisted cursor does not match receipt")
    replayed = SolanaCursorAdvanceReceipt(
        receipt_id=receipt.receipt_id,
        previous_cursor_id=receipt.previous_cursor_id,
        current_cursor_id=receipt.current_cursor_id,
        observation_id=observation.observation_id,
        advanced=receipt.advanced,
    )
    if replayed != receipt:
        raise ValueError("cursor advance receipt does not match replay")
    return SolanaCursorAdvanceReplayReceipt(
        receipt_id=deterministic_id(
            "solana_cursor_advance_replay",
            {
                "original_receipt_id": receipt.receipt_id,
                "schema_version": "solana_cursor_advance_replay.v1",
            },
        ),
        original_receipt_id=receipt.receipt_id,
        matches=True,
    )


__all__ = [
    "SolanaCursorAdvanceReceipt",
    "SolanaCursorAdvanceReplayReceipt",
    "advance_and_persist_solana_cursor",
    "verify_solana_cursor_advance_replay",
]
