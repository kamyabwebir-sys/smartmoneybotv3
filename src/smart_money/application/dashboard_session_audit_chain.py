from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from smart_money.application.dashboard_audit_recovery_gate import (
    DashboardAuditRecoveryReceipt,
)
from smart_money.application.dashboard_query_audit_receipt import (
    DashboardQueryAuditReceipt,
)
from smart_money.application.dashboard_recovery_query_session import (
    DashboardRecoveryQuerySessionReceipt,
)
from smart_money.application.dashboard_recovery_session_replay_verifier import (
    DashboardSessionReplayReceipt,
)
from smart_money.core.serialization import canonical_json


@dataclass(frozen=True, slots=True)
class DashboardSessionAuditEntry:
    entry_kind: str
    entry_id: str
    parent_id: str | None
    schema_version: str = "dashboard_session_audit_entry.v1"

    def __post_init__(self) -> None:
        for name in ("entry_kind", "entry_id"):
            if not isinstance(getattr(self, name), str) or not getattr(
                self, name
            ).strip():
                raise ValueError(f"{name} must be non-empty")
        if self.parent_id is not None and not isinstance(self.parent_id, str):
            raise TypeError("parent_id must be a string or None")
        if self.schema_version != "dashboard_session_audit_entry.v1":
            raise ValueError("unsupported session audit entry schema_version")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "entry_kind": self.entry_kind,
            "parent_id": self.parent_id,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class DashboardSessionAuditChain:
    entries: tuple[DashboardSessionAuditEntry, ...]
    chain_hash: str
    schema_version: str = "dashboard_session_audit_chain.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.entries, tuple) or not all(
            isinstance(item, DashboardSessionAuditEntry) for item in self.entries
        ):
            raise TypeError("entries must be a tuple of audit entries")
        if self.chain_hash != _chain_hash(self.entries):
            raise ValueError("session audit chain hash mismatch")
        if self.schema_version != "dashboard_session_audit_chain.v1":
            raise ValueError("unsupported session audit chain schema_version")

    @classmethod
    def from_receipts(
        cls,
        recovery: DashboardAuditRecoveryReceipt,
        query: DashboardQueryAuditReceipt,
        session: DashboardRecoveryQuerySessionReceipt,
        replay: DashboardSessionReplayReceipt,
    ) -> DashboardSessionAuditChain:
        entries = (
            DashboardSessionAuditEntry("recovery", recovery.receipt_id, None),
            DashboardSessionAuditEntry("query", query.receipt_id, recovery.receipt_id),
            DashboardSessionAuditEntry("session", session.session_id, query.receipt_id),
            DashboardSessionAuditEntry("replay", replay.verification_id, session.session_id),
        )
        return cls(entries=entries, chain_hash=_chain_hash(entries))

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "chain_hash": self.chain_hash,
            "entries": [item.canonical_dict() for item in self.entries],
            "schema_version": self.schema_version,
        }

    @property
    def chain_id(self) -> str:
        return hashlib.sha256(
            canonical_json(self.canonical_dict()).encode("utf-8")
        ).hexdigest()


def _chain_hash(entries: tuple[DashboardSessionAuditEntry, ...]) -> str:
    previous = "0" * 64
    for entry in entries:
        previous = hashlib.sha256(
            canonical_json(
                {"previous_hash": previous, "entry": entry.canonical_dict()}
            ).encode("utf-8")
        ).hexdigest()
    return previous


__all__ = ["DashboardSessionAuditChain", "DashboardSessionAuditEntry"]
