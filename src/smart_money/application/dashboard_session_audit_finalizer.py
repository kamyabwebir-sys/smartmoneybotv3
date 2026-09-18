from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.dashboard_session_audit_chain import (
    DashboardSessionAuditChain,
)
from smart_money.application.dashboard_session_audit_head_anchor import (
    DashboardSessionAuditHeadAnchor,
)
from smart_money.application.dashboard_session_recovery_gate import (
    DashboardSessionRecoveryReceipt,
)
from smart_money.application.dashboard_session_recovery_replay_verifier import (
    DashboardSessionRecoveryReplayReceipt,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class DashboardSessionAuditFinalReceipt:
    chain_id: str
    chain_hash: str
    head_anchor_id: str
    recovery_receipt_id: str
    recovery_replay_verification_id: str
    entry_count: int
    decision: str
    reason_code: str
    schema_version: str = "dashboard_session_audit_final.v1"

    def __post_init__(self) -> None:
        for name in (
            "chain_id",
            "chain_hash",
            "head_anchor_id",
            "recovery_receipt_id",
            "recovery_replay_verification_id",
            "reason_code",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        if len(self.chain_hash) != 64:
            raise ValueError("chain_hash must be a SHA-256 hex digest")
        if not isinstance(self.entry_count, int) or isinstance(
            self.entry_count, bool
        ) or self.entry_count < 0:
            raise ValueError("entry_count must be non-negative")
        if self.decision not in {"READY", "BLOCKED"}:
            raise ValueError("decision must be READY or BLOCKED")
        if self.schema_version != "dashboard_session_audit_final.v1":
            raise ValueError("unsupported session audit final schema_version")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "chain_hash": self.chain_hash,
            "chain_id": self.chain_id,
            "decision": self.decision,
            "entry_count": self.entry_count,
            "head_anchor_id": self.head_anchor_id,
            "reason_code": self.reason_code,
            "recovery_receipt_id": self.recovery_receipt_id,
            "recovery_replay_verification_id": self.recovery_replay_verification_id,
            "schema_version": self.schema_version,
        }

    @property
    def receipt_id(self) -> str:
        return deterministic_id(
            "dashboard_session_audit_final",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardSessionAuditChainFinalizer:
    def finalize(
        self,
        chain: DashboardSessionAuditChain | None,
        anchor: DashboardSessionAuditHeadAnchor | None,
        recovery: DashboardSessionRecoveryReceipt,
        replay: DashboardSessionRecoveryReplayReceipt,
    ) -> DashboardSessionAuditFinalReceipt:
        if not isinstance(recovery, DashboardSessionRecoveryReceipt):
            raise TypeError("recovery must be a DashboardSessionRecoveryReceipt")
        if not isinstance(replay, DashboardSessionRecoveryReplayReceipt):
            raise TypeError(
                "replay must be a DashboardSessionRecoveryReplayReceipt"
            )
        if chain is None or anchor is None:
            return self._blocked(
                chain,
                anchor,
                recovery,
                replay,
                "MISSING_SESSION_CHAIN_OR_ANCHOR",
            )
        if not anchor.matches(chain):
            return self._blocked(
                chain,
                anchor,
                recovery,
                replay,
                "SESSION_CHAIN_HEAD_MISMATCH",
            )
        if recovery.decision != "READY":
            return self._blocked(
                chain,
                anchor,
                recovery,
                replay,
                "SESSION_RECOVERY_NOT_READY",
            )
        if recovery.anchor_id != anchor.anchor_id or recovery.chain_id != chain.chain_id:
            return self._blocked(
                chain,
                anchor,
                recovery,
                replay,
                "SESSION_RECOVERY_LINKAGE_MISMATCH",
            )
        if not replay.matches:
            return self._blocked(
                chain,
                anchor,
                recovery,
                replay,
                "SESSION_RECOVERY_REPLAY_MISMATCH",
            )
        if replay.expected_receipt_id != recovery.receipt_id:
            return self._blocked(
                chain,
                anchor,
                recovery,
                replay,
                "SESSION_RECOVERY_REPLAY_EXPECTED_ID_MISMATCH",
            )
        return DashboardSessionAuditFinalReceipt(
            chain_id=chain.chain_id,
            chain_hash=chain.chain_hash,
            head_anchor_id=anchor.anchor_id,
            recovery_receipt_id=recovery.receipt_id,
            recovery_replay_verification_id=replay.verification_id,
            entry_count=len(chain.entries),
            decision="READY",
            reason_code="SESSION_AUDIT_CHAIN_FINALIZED",
        )

    @staticmethod
    def _blocked(
        chain: DashboardSessionAuditChain | None,
        anchor: DashboardSessionAuditHeadAnchor | None,
        recovery: DashboardSessionRecoveryReceipt,
        replay: DashboardSessionRecoveryReplayReceipt,
        reason_code: str,
    ) -> DashboardSessionAuditFinalReceipt:
        return DashboardSessionAuditFinalReceipt(
            chain_id=chain.chain_id if chain is not None else "missing-chain",
            chain_hash=chain.chain_hash if chain is not None else "0" * 64,
            head_anchor_id=anchor.anchor_id if anchor is not None else "missing-anchor",
            recovery_receipt_id=recovery.receipt_id,
            recovery_replay_verification_id=replay.verification_id,
            entry_count=len(chain.entries) if chain is not None else 0,
            decision="BLOCKED",
            reason_code=reason_code,
        )


__all__ = [
    "DashboardSessionAuditChainFinalizer",
    "DashboardSessionAuditFinalReceipt",
]
