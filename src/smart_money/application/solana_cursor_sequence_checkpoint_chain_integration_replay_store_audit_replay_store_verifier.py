from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_store import (
    JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayStore,
    SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayReceipt,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayStoreVerificationReceipt:
    verification_id: str
    replay_id: str
    matches: bool
    schema_version: str = (
        "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay_store_verification.v1"
    )

    def __post_init__(self) -> None:
        if not isinstance(self.replay_id, str) or not self.replay_id.strip():
            raise ValueError("replay_id must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != (
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay_store_verification.v1"
        ):
            raise ValueError("unsupported verification schema_version")
        expected = deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay_store_verification",
            {
                "matches": self.matches,
                "replay_id": self.replay_id,
                "schema_version": self.schema_version,
            },
        )
        if self.verification_id != expected:
            raise ValueError("verification_id does not match deterministic payload")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "matches": self.matches,
            "replay_id": self.replay_id,
            "schema_version": self.schema_version,
            "verification_id": self.verification_id,
        }


def verify_solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay_store(
    store: JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayStore,
    expected: SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayReceipt,
) -> SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayStoreVerificationReceipt:
    if not isinstance(
        store,
        JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayStore,
    ):
        raise TypeError("store must be an audit replay store")
    if not isinstance(
        expected,
        SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayReceipt,
    ):
        raise TypeError("expected must be an audit replay receipt")
    actual = store.load()
    if actual is None:
        raise ValueError("persisted audit replay receipt is missing")
    if actual.canonical_dict() != expected.canonical_dict():
        raise ValueError("persisted audit replay receipt does not match verifier input")
    verification_id = deterministic_id(
        "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay_store_verification",
        {
            "matches": True,
            "replay_id": actual.replay_id,
            "schema_version": (
                "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay_store_verification.v1"
            ),
        },
    )
    return SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayStoreVerificationReceipt(
        verification_id=verification_id,
        replay_id=actual.replay_id,
        matches=True,
    )


__all__ = [
    "SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayStoreVerificationReceipt",
    "verify_solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay_store",
]
