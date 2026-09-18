from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReceipt:
    verification_id: str
    replay_id: str
    matches: bool
    schema_version: str = "solana_verification_replay_store_persistence_audit_replay_store_verification.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.replay_id, str) or not self.replay_id.strip():
            raise ValueError("replay_id must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        expected = deterministic_id(
            "solana_verification_replay_store_persistence_audit_replay_store_verification",
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


def verify_solana_verification_replay_store_persistence_audit_replay_store(
    store: Any, expected: Any
) -> SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReceipt:
    from smart_money.adapters.persistence.solana_verification_replay_store_persistence_audit_replay_store import (
        JsonSolanaVerificationReplayStorePersistenceAuditReplayStore,
    )
    from smart_money.application.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay_store_audit import (
        SolanaVerificationReplayStorePersistenceAuditReplayReceipt,
    )

    if not isinstance(store, JsonSolanaVerificationReplayStorePersistenceAuditReplayStore):
        raise TypeError("store must be a verification audit replay store")
    if not isinstance(expected, SolanaVerificationReplayStorePersistenceAuditReplayReceipt):
        raise TypeError("expected must be a verification audit replay audit receipt")
    actual = store.load()
    if actual is None:
        raise ValueError("persisted verification audit replay receipt is missing")
    if actual.canonical_dict() != expected.canonical_dict():
        raise ValueError("persisted verification audit replay receipt does not match verifier input")
    schema = "solana_verification_replay_store_persistence_audit_replay_store_verification.v1"
    return SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReceipt(
        verification_id=deterministic_id(
            "solana_verification_replay_store_persistence_audit_replay_store_verification",
            {"matches": True, "replay_id": actual.replay_id, "schema_version": schema},
        ),
        replay_id=actual.replay_id,
        matches=True,
    )


__all__ = [
    "SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReceipt",
    "verify_solana_verification_replay_store_persistence_audit_replay_store",
]
