from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from smart_money.application.dashboard_session_audit_chain import (
    DashboardSessionAuditEntry,
)
from smart_money.application.dashboard_session_final_audit_chain import (
    DashboardSessionFinalAuditChain,
)
from smart_money.application.dashboard_session_final_audit_recovery_gate import (
    DashboardSessionFinalAuditRecoveryReceipt,
)
from smart_money.application.dashboard_session_final_audit_recovery_replay_verifier import (
    DashboardSessionFinalAuditRecoveryReplayReceipt,
)
from smart_money.core.serialization import canonical_json


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryAuditChain:
    entries: tuple[DashboardSessionAuditEntry, ...]
    chain_hash: str
    schema_version: str = "dashboard_session_final_recovery_audit_chain.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.entries, tuple) or not all(
            isinstance(item, DashboardSessionAuditEntry) for item in self.entries
        ):
            raise TypeError("entries must be a tuple of audit entries")
        if self.chain_hash != _chain_hash(self.entries):
            raise ValueError("final recovery audit chain hash mismatch")
        if (
            self.schema_version
            != "dashboard_session_final_recovery_audit_chain.v1"
        ):
            raise ValueError(
                "unsupported final recovery audit chain schema_version"
            )

    @classmethod
    def from_chain(
        cls,
        chain: DashboardSessionFinalAuditChain,
        recovery: DashboardSessionFinalAuditRecoveryReceipt,
        replay: DashboardSessionFinalAuditRecoveryReplayReceipt,
    ) -> DashboardSessionFinalRecoveryAuditChain:
        if not isinstance(chain, DashboardSessionFinalAuditChain):
            raise TypeError("chain must be a DashboardSessionFinalAuditChain")
        if not isinstance(
            recovery, DashboardSessionFinalAuditRecoveryReceipt
        ):
            raise TypeError(
                "recovery must be a DashboardSessionFinalAuditRecoveryReceipt"
            )
        if not isinstance(
            replay, DashboardSessionFinalAuditRecoveryReplayReceipt
        ):
            raise TypeError(
                "replay must be a DashboardSessionFinalAuditRecoveryReplayReceipt"
            )
        if recovery.decision != "READY":
            raise ValueError("cannot integrate a blocked recovery receipt")
        if recovery.chain_id != chain.chain_id:
            raise ValueError("recovery receipt is not linked to final chain")
        if not replay.matches:
            raise ValueError("cannot integrate a non-matching recovery replay")
        if replay.expected_receipt_id != recovery.receipt_id:
            raise ValueError("recovery replay is not linked to recovery receipt")
        parent = chain.entries[-1].entry_id if chain.entries else None
        entries = chain.entries + (
            DashboardSessionAuditEntry("recovery", recovery.receipt_id, parent),
            DashboardSessionAuditEntry(
                "recovery_replay",
                replay.verification_id,
                recovery.receipt_id,
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


__all__ = ["DashboardSessionFinalRecoveryAuditChain"]
