from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_binding_store import (
    JsonSolanaCursorSequenceCheckpointBindingStore,
)
from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_store import (
    JsonSolanaCursorSequenceCheckpointStore,
)
from smart_money.adapters.persistence.solana_observation_sequence_store import (
    JsonSolanaObservationSequenceStore,
)
from smart_money.adapters.persistence.solana_slot_cursor_store import JsonSolanaSlotCursorStore
from smart_money.application.solana_cursor_sequence_checkpoint_binding import (
    SolanaCursorSequenceCheckpointBindingReceipt,
)
from smart_money.core.ids import deterministic_id
from smart_money.domain.solana_observation import (
    SolanaChainObservation,
    SolanaCursorSequenceCheckpoint,
    replay_solana_observation_order,
)


@dataclass(frozen=True, slots=True)
class SolanaCursorSequenceCheckpointChainIntegrationReceipt:
    receipt_id: str
    sequence_id: str
    checkpoint_id: str
    binding_receipt_id: str
    cursor_id: str
    observation_id: str
    schema_version: str = "solana_cursor_sequence_checkpoint_chain_integration.v1"

    def __post_init__(self) -> None:
        for name in (
            "receipt_id", "sequence_id", "checkpoint_id", "binding_receipt_id",
            "cursor_id", "observation_id",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.schema_version != "solana_cursor_sequence_checkpoint_chain_integration.v1":
            raise ValueError("unsupported Solana chain integration schema_version")
        expected = deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration",
            self.identity_payload(),
        )
        if self.receipt_id != expected:
            raise ValueError("receipt_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "binding_receipt_id": self.binding_receipt_id,
            "checkpoint_id": self.checkpoint_id,
            "cursor_id": self.cursor_id,
            "observation_id": self.observation_id,
            "schema_version": self.schema_version,
            "sequence_id": self.sequence_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}


def integrate_solana_cursor_sequence_checkpoint_chain(
    cursor_store: JsonSolanaSlotCursorStore,
    sequence_store: JsonSolanaObservationSequenceStore,
    checkpoint_store: JsonSolanaCursorSequenceCheckpointStore,
    binding_store: JsonSolanaCursorSequenceCheckpointBindingStore,
    observations: tuple[SolanaChainObservation, ...],
    binding_receipt: SolanaCursorSequenceCheckpointBindingReceipt,
) -> SolanaCursorSequenceCheckpointChainIntegrationReceipt:
    if not isinstance(binding_receipt, SolanaCursorSequenceCheckpointBindingReceipt):
        raise TypeError("binding_receipt must be a SolanaCursorSequenceCheckpointBindingReceipt")
    if not isinstance(observations, tuple) or not observations:
        raise ValueError("observations must be a non-empty tuple")
    sequence = replay_solana_observation_order(observations)
    cursor = cursor_store.load()
    checkpoint = checkpoint_store.load()
    stored_binding = binding_store.load()
    if stored_binding != binding_receipt:
        raise ValueError("persisted Solana binding receipt does not match integration")
    if sequence_store.get(sequence.sequence_id) != sequence:
        raise ValueError("persisted Solana sequence does not match integration")
    if checkpoint is None:
        raise ValueError("persisted Solana checkpoint is missing")
    expected_checkpoint = SolanaCursorSequenceCheckpoint.from_sequence(sequence, cursor)
    if checkpoint != expected_checkpoint:
        raise ValueError("persisted Solana checkpoint does not match integration")
    if (
        binding_receipt.sequence_id != sequence.sequence_id
        or binding_receipt.checkpoint_id != checkpoint.checkpoint_id
        or binding_receipt.current_cursor_id != cursor.canonical_id
        or binding_receipt.observation_id != observations[-1].observation_id
    ):
        raise ValueError("Solana binding receipt does not match integration")
    identity = {
        "binding_receipt_id": binding_receipt.receipt_id,
        "checkpoint_id": checkpoint.checkpoint_id,
        "cursor_id": cursor.canonical_id,
        "observation_id": observations[-1].observation_id,
        "schema_version": "solana_cursor_sequence_checkpoint_chain_integration.v1",
        "sequence_id": sequence.sequence_id,
    }
    return SolanaCursorSequenceCheckpointChainIntegrationReceipt(
        receipt_id=deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration", identity
        ),
        sequence_id=sequence.sequence_id,
        checkpoint_id=checkpoint.checkpoint_id,
        binding_receipt_id=binding_receipt.receipt_id,
        cursor_id=cursor.canonical_id,
        observation_id=observations[-1].observation_id,
    )


__all__ = [
    "SolanaCursorSequenceCheckpointChainIntegrationReceipt",
    "integrate_solana_cursor_sequence_checkpoint_chain",
]
