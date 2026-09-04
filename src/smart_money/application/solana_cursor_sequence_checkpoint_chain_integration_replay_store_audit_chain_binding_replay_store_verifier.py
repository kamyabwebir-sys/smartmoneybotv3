from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReceipt:
    verification_id: str
    replay_id: str
    matches: bool
    schema_version: str = "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.replay_id, str) or not self.replay_id.strip():
            raise ValueError("replay_id must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        expected = deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification",
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


@dataclass(frozen=True, slots=True)
class SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayStoreVerificationReceipt:
    verification_id: str
    replay_id: str
    matches: bool
    schema_version: str = "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay_store_verification.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.replay_id, str) or not self.replay_id.strip():
            raise ValueError("replay_id must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        expected = deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay_store_verification",
            {"matches": self.matches, "replay_id": self.replay_id, "schema_version": self.schema_version},
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

def verify_solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay_store(
    store: Any,
    expected: Any,
) -> SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayStoreVerificationReceipt:
    from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_store import (
        JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayStore,
        SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayReceipt,
    )
    if not isinstance(store, JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayStore):
        raise TypeError("store must be a verification replay store")
    if not isinstance(expected, SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayReceipt):
        raise TypeError("expected must be a verification replay receipt")
    actual = store.load()
    if actual is None:
        raise ValueError("persisted verification replay receipt is missing")
    if actual.canonical_dict() != expected.canonical_dict():
        raise ValueError("persisted verification replay receipt does not match verifier input")
    schema = "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay_store_verification.v1"
    return SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayStoreVerificationReceipt(
        verification_id=deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay_store_verification",
            {"matches": True, "replay_id": actual.replay_id, "schema_version": schema},
        ),
        replay_id=actual.replay_id,
        matches=True,
    )


__all__ = [
    "SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReceipt",
    "SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayStoreVerificationReceipt",
    "verify_solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay_store",
]
