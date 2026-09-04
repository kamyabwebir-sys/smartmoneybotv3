from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.dashboard_session_final_audit_chain import (
    DashboardSessionFinalAuditChain,
)
from smart_money.application.dashboard_session_final_audit_chain_replay_verifier import (
    DashboardSessionFinalAuditChainReplayReceipt,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalAuditRecoveryReceipt:
    decision: str
    reason_code: str
    chain_id: str | None
    replay_verification_id: str | None
    schema_version: str = "dashboard_session_final_audit_recovery.v1"

    def __post_init__(self) -> None:
        if self.decision not in {"READY", "BLOCKED"}:
            raise ValueError("decision must be READY or BLOCKED")
        if not isinstance(self.reason_code, str) or not self.reason_code.strip():
            raise ValueError("reason_code must be non-empty")
        for name in ("chain_id", "replay_verification_id"):
            value = getattr(self, name)
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                raise ValueError(f"{name} must be non-empty or None")
        if self.schema_version != "dashboard_session_final_audit_recovery.v1":
            raise ValueError(
                "unsupported session final audit recovery schema_version"
            )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "decision": self.decision,
            "reason_code": self.reason_code,
            "replay_verification_id": self.replay_verification_id,
            "schema_version": self.schema_version,
        }

    @property
    def receipt_id(self) -> str:
        return deterministic_id(
            "dashboard_session_final_audit_recovery",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalAuditRecoveryGate:
    def evaluate(
        self,
        chain: DashboardSessionFinalAuditChain | None,
        replay: DashboardSessionFinalAuditChainReplayReceipt | None,
        persisted_replay: DashboardSessionFinalAuditChainReplayReceipt | None,
    ) -> DashboardSessionFinalAuditRecoveryReceipt:
        if chain is None or replay is None:
            return self._blocked(
                chain,
                replay,
                "MISSING_FINAL_AUDIT_CHAIN_OR_REPLAY",
            )
        if not replay.matches:
            return self._blocked(
                chain,
                replay,
                "FINAL_AUDIT_CHAIN_REPLAY_MISMATCH",
            )
        if replay.expected_chain_id != chain.chain_id:
            return self._blocked(
                chain,
                replay,
                "FINAL_AUDIT_CHAIN_EXPECTED_ID_MISMATCH",
            )
        if replay.actual_chain_id != chain.chain_id:
            return self._blocked(
                chain,
                replay,
                "FINAL_AUDIT_CHAIN_ACTUAL_ID_MISMATCH",
            )
        if persisted_replay is None:
            return self._blocked(
                chain,
                replay,
                "MISSING_PERSISTED_FINAL_AUDIT_REPLAY",
            )
        if persisted_replay != replay:
            return self._blocked(
                chain,
                replay,
                "PERSISTED_FINAL_AUDIT_REPLAY_MISMATCH",
            )
        return DashboardSessionFinalAuditRecoveryReceipt(
            decision="READY",
            reason_code="FINAL_AUDIT_CHAIN_RECOVERY_VERIFIED",
            chain_id=chain.chain_id,
            replay_verification_id=replay.verification_id,
        )

    @staticmethod
    def _blocked(
        chain: DashboardSessionFinalAuditChain | None,
        replay: DashboardSessionFinalAuditChainReplayReceipt | None,
        reason_code: str,
    ) -> DashboardSessionFinalAuditRecoveryReceipt:
        return DashboardSessionFinalAuditRecoveryReceipt(
            decision="BLOCKED",
            reason_code=reason_code,
            chain_id=None if chain is None else chain.chain_id,
            replay_verification_id=(
                None if replay is None else replay.verification_id
            ),
        )


__all__ = [
    "DashboardSessionFinalAuditRecoveryGate",
    "DashboardSessionFinalAuditRecoveryReceipt",
]
