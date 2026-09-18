from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_store import (
    JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayStore,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class SolanaVerificationReplayStorePersistenceAuditReplayReceipt:
    replay_id: str
    original_audit_id: str
    matches: bool
    schema_version: str = "solana_verification_replay_store_persistence_audit_replay.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.original_audit_id, str) or not self.original_audit_id.strip():
            raise ValueError("original_audit_id must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        expected = deterministic_id(
            "solana_verification_replay_store_persistence_audit_replay",
            {"original_audit_id": self.original_audit_id, "schema_version": self.schema_version},
        )
        if self.replay_id != expected:
            raise ValueError("replay_id does not match deterministic payload")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "matches": self.matches,
            "original_audit_id": self.original_audit_id,
            "replay_id": self.replay_id,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class SolanaVerificationReplayStorePersistenceAuditReceipt:
    expected_replay_id: str
    persisted_replay_id: str | None
    file_exists: bool
    matches: bool
    mismatches: tuple[str, ...] = ()
    schema_version: str = "solana_verification_replay_store_persistence_audit.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.expected_replay_id, str) or not self.expected_replay_id.strip():
            raise ValueError("expected_replay_id must be non-empty")
        if self.persisted_replay_id is not None and not self.persisted_replay_id.strip():
            raise ValueError("persisted_replay_id must be non-empty or None")
        if not isinstance(self.file_exists, bool) or not isinstance(self.matches, bool):
            raise TypeError("file_exists and matches must be boolean")
        if not isinstance(self.mismatches, tuple):
            raise TypeError("mismatches must be a tuple")
        if self.matches and self.mismatches:
            raise ValueError("matching audit cannot contain mismatches")
        if not self.matches and not self.mismatches:
            raise ValueError("non-matching audit requires mismatches")

    @property
    def audit_id(self) -> str:
        return deterministic_id(
            "solana_verification_replay_store_persistence_audit",
            self.canonical_dict(),
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "expected_replay_id": self.expected_replay_id,
            "file_exists": self.file_exists,
            "matches": self.matches,
            "mismatches": list(self.mismatches),
            "persisted_replay_id": self.persisted_replay_id,
            "schema_version": self.schema_version,
        }


def audit_solana_verification_replay_store_persistence(
    store: JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayStore,
    expected: Any,
) -> SolanaVerificationReplayStorePersistenceAuditReceipt:
    if not isinstance(store, JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayStore):
        raise TypeError("store must be a verification replay store")
    if not isinstance(expected, type(store.load())):
        raise TypeError("expected must be a verification replay receipt")
    actual = store.load()
    mismatches: list[str] = []
    if actual is None:
        mismatches.append("persisted verification replay receipt is missing")
    elif actual.canonical_dict() != expected.canonical_dict():
        mismatches.append("persisted verification replay receipt does not match expected")
    return SolanaVerificationReplayStorePersistenceAuditReceipt(
        expected_replay_id=expected.replay_id,
        persisted_replay_id=None if actual is None else actual.replay_id,
        file_exists=Path(store._file_path).is_file(),  # type: ignore[attr-defined]
        matches=not mismatches,
        mismatches=tuple(mismatches),
    )


def replay_solana_verification_replay_store_persistence_audit(
    expected: SolanaVerificationReplayStorePersistenceAuditReceipt,
    actual: SolanaVerificationReplayStorePersistenceAuditReceipt,
) -> SolanaVerificationReplayStorePersistenceAuditReplayReceipt:
    if not isinstance(expected, SolanaVerificationReplayStorePersistenceAuditReceipt):
        raise TypeError("expected must be a persistence audit receipt")
    if not isinstance(actual, SolanaVerificationReplayStorePersistenceAuditReceipt):
        raise TypeError("actual must be a persistence audit receipt")
    if expected.canonical_dict() != actual.canonical_dict():
        raise ValueError("persistence audit receipt does not match replay")
    return SolanaVerificationReplayStorePersistenceAuditReplayReceipt(
        replay_id=deterministic_id(
            "solana_verification_replay_store_persistence_audit_replay",
            {
                "original_audit_id": expected.audit_id,
                "schema_version": "solana_verification_replay_store_persistence_audit_replay.v1",
            },
        ),
        original_audit_id=expected.audit_id,
        matches=True,
    )


__all__ = [
    "SolanaVerificationReplayStorePersistenceAuditReceipt",
    "audit_solana_verification_replay_store_persistence",
    "SolanaVerificationReplayStorePersistenceAuditReplayReceipt",
    "replay_solana_verification_replay_store_persistence_audit",
]
