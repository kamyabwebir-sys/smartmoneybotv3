from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReplayReceipt:
    verification_id: str
    replay_id: str
    matches: bool
    schema_version: str = (
        "solana_verification_replay_store_persistence_audit_replay_store_verification_replay.v1"
    )

    def __post_init__(self) -> None:
        if not isinstance(self.replay_id, str) or not self.replay_id.strip():
            raise ValueError("replay_id must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        expected = deterministic_id(
            "solana_verification_replay_store_persistence_audit_replay_store_verification_replay",
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


def replay_verify_solana_verification_replay_store_persistence_audit_replay_store_verification(
    store: Any, expected: Any
) -> SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReplayReceipt:
    from smart_money.adapters.persistence.solana_verification_replay_store_persistence_audit_replay_store_verification_store import (
        JsonSolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationStore,
    )
    from smart_money.application.solana_verification_replay_store_persistence_audit_replay_store_verifier import (
        SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReceipt,
    )

    if not isinstance(
        store,
        JsonSolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationStore,
    ):
        raise TypeError("store must be a verification receipt store")
    if not isinstance(
        expected,
        SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReceipt,
    ):
        raise TypeError("expected must be a verification receipt")
    actual = store.load()
    if actual is None:
        raise ValueError("persisted verification receipt is missing")
    if actual.canonical_dict() != expected.canonical_dict():
        raise ValueError("persisted verification receipt does not match replay input")
    schema = (
        "solana_verification_replay_store_persistence_audit_replay_store_verification_replay.v1"
    )
    return SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReplayReceipt(
        verification_id=deterministic_id(
            "solana_verification_replay_store_persistence_audit_replay_store_verification_replay",
            {"matches": True, "replay_id": actual.replay_id, "schema_version": schema},
        ),
        replay_id=actual.replay_id,
        matches=True,
    )


__all__ = [
    "SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReplayReceipt",
    "replay_verify_solana_verification_replay_store_persistence_audit_replay_store_verification",
]
