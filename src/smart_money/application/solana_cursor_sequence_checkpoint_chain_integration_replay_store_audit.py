from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_chain_integration_store import (
    JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStore,
    SolanaCursorSequenceCheckpointChainIntegrationReplayReceipt,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReceipt:
    expected_replay_id: str
    persisted_replay_id: str | None
    matches: bool
    file_exists: bool
    mismatches: tuple[str, ...] = ()
    schema_version: str = "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.expected_replay_id, str) or not self.expected_replay_id.strip():
            raise ValueError("expected_replay_id must be non-empty")
        if self.persisted_replay_id is not None and not self.persisted_replay_id.strip():
            raise ValueError("persisted_replay_id must be non-empty or None")
        if not isinstance(self.matches, bool) or not isinstance(self.file_exists, bool):
            raise TypeError("matches and file_exists must be boolean")
        if not isinstance(self.mismatches, tuple):
            raise TypeError("mismatches must be a tuple")
        if self.matches and self.mismatches:
            raise ValueError("matching audit cannot contain mismatches")
        if not self.matches and not self.mismatches:
            raise ValueError("non-matching audit requires mismatches")
        if self.schema_version != "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit.v1":
            raise ValueError("unsupported replay store audit schema_version")

    @property
    def audit_id(self) -> str:
        return deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit",
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


def audit_solana_cursor_sequence_checkpoint_chain_integration_replay_store(
    store: JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStore,
    expected: SolanaCursorSequenceCheckpointChainIntegrationReplayReceipt,
) -> SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReceipt:
    if not isinstance(store, JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStore):
        raise TypeError("store must be a Solana replay store")
    if not isinstance(expected, SolanaCursorSequenceCheckpointChainIntegrationReplayReceipt):
        raise TypeError("expected must be a replay receipt")
    actual = store.load()
    mismatches: list[str] = []
    if actual is None:
        mismatches.append("persisted replay receipt is missing")
    elif actual.canonical_dict() != expected.canonical_dict():
        mismatches.append("persisted replay receipt does not match expected")
    matches = not mismatches
    return SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReceipt(
        expected_replay_id=expected.replay_id,
        persisted_replay_id=None if actual is None else actual.replay_id,
        matches=matches,
        file_exists=Path(store._file_path).is_file(),  # type: ignore[attr-defined]
        mismatches=tuple(mismatches),
    )


__all__ = [
    "SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReceipt",
    "audit_solana_cursor_sequence_checkpoint_chain_integration_replay_store",
]
