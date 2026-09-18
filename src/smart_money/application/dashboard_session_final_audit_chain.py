from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from smart_money.application.dashboard_session_audit_chain import (
    DashboardSessionAuditChain,
    DashboardSessionAuditEntry,
)
from smart_money.application.dashboard_session_audit_final_replay_verifier import (
    DashboardSessionAuditFinalReplayReceipt,
)
from smart_money.application.dashboard_session_audit_finalizer import (
    DashboardSessionAuditFinalReceipt,
)
from smart_money.core.serialization import canonical_json


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalAuditChain:
    entries: tuple[DashboardSessionAuditEntry, ...]
    chain_hash: str
    schema_version: str = "dashboard_session_final_audit_chain.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.entries, tuple) or not all(
            isinstance(item, DashboardSessionAuditEntry) for item in self.entries
        ):
            raise TypeError("entries must be a tuple of audit entries")
        if self.chain_hash != _chain_hash(self.entries):
            raise ValueError("final audit chain hash mismatch")
        if self.schema_version != "dashboard_session_final_audit_chain.v1":
            raise ValueError("unsupported final audit chain schema_version")

    @classmethod
    def from_chain(
        cls,
        chain: DashboardSessionAuditChain,
        final: DashboardSessionAuditFinalReceipt,
        replay: DashboardSessionAuditFinalReplayReceipt,
    ) -> DashboardSessionFinalAuditChain:
        if not isinstance(chain, DashboardSessionAuditChain):
            raise TypeError("chain must be a DashboardSessionAuditChain")
        if not isinstance(final, DashboardSessionAuditFinalReceipt):
            raise TypeError("final must be a DashboardSessionAuditFinalReceipt")
        if not isinstance(replay, DashboardSessionAuditFinalReplayReceipt):
            raise TypeError(
                "replay must be a DashboardSessionAuditFinalReplayReceipt"
            )
        if not replay.matches:
            raise ValueError("cannot integrate a non-matching final replay")
        if replay.expected_receipt_id != final.receipt_id:
            raise ValueError("final replay is not linked to final receipt")
        if final.chain_id != chain.chain_id or final.chain_hash != chain.chain_hash:
            raise ValueError("final receipt is not linked to source chain")
        parent = chain.entries[-1].entry_id if chain.entries else None
        entries = chain.entries + (
            DashboardSessionAuditEntry("final", final.receipt_id, parent),
            DashboardSessionAuditEntry(
                "final_replay", replay.verification_id, final.receipt_id
            ),
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


__all__ = ["DashboardSessionFinalAuditChain"]
