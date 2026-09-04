from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_chain_replay_verifier as replay_model,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_chain import (
    DashboardSessionFinalRecoveryGateAuditChain,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditRecoveryReceipt:
    decision: str
    reason_code: str
    chain_id: str | None
    replay_verification_id: str | None
    schema_version: str = (
        "dashboard_session_final_recovery_gate_audit_recovery.v1"
    )

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
        if (
            self.schema_version
            != "dashboard_session_final_recovery_gate_audit_recovery.v1"
        ):
            raise ValueError(
                "unsupported final recovery gate audit recovery schema_version"
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
            "dashboard_session_final_recovery_gate_audit_recovery",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditRecoveryGate:
    def evaluate(
        self,
        chain: DashboardSessionFinalRecoveryGateAuditChain | None,
        replay: replay_model.DashboardSessionFinalRecoveryGateAuditChainReplayReceipt | None,
        persisted_replay: (
            replay_model.DashboardSessionFinalRecoveryGateAuditChainReplayReceipt
            | None
        ),
    ) -> DashboardSessionFinalRecoveryGateAuditRecoveryReceipt:
        if chain is None or replay is None:
            return self._blocked(
                chain, replay, "MISSING_GATE_AUDIT_CHAIN_OR_REPLAY"
            )
        if not replay.matches:
            return self._blocked(
                chain, replay, "GATE_AUDIT_CHAIN_REPLAY_MISMATCH"
            )
        if replay.expected_chain_id != chain.chain_id:
            return self._blocked(
                chain, replay, "GATE_AUDIT_CHAIN_EXPECTED_ID_MISMATCH"
            )
        if replay.actual_chain_id != chain.chain_id:
            return self._blocked(
                chain, replay, "GATE_AUDIT_CHAIN_ACTUAL_ID_MISMATCH"
            )
        if persisted_replay is None:
            return self._blocked(
                chain, replay, "MISSING_PERSISTED_GATE_AUDIT_REPLAY"
            )
        if persisted_replay != replay:
            return self._blocked(
                chain, replay, "PERSISTED_GATE_AUDIT_REPLAY_MISMATCH"
            )
        return DashboardSessionFinalRecoveryGateAuditRecoveryReceipt(
            decision="READY",
            reason_code="GATE_AUDIT_CHAIN_RECOVERY_VERIFIED",
            chain_id=chain.chain_id,
            replay_verification_id=replay.verification_id,
        )

    @staticmethod
    def _blocked(
        chain: DashboardSessionFinalRecoveryGateAuditChain | None,
        replay: replay_model.DashboardSessionFinalRecoveryGateAuditChainReplayReceipt | None,
        reason_code: str,
    ) -> DashboardSessionFinalRecoveryGateAuditRecoveryReceipt:
        return DashboardSessionFinalRecoveryGateAuditRecoveryReceipt(
            decision="BLOCKED",
            reason_code=reason_code,
            chain_id=None if chain is None else chain.chain_id,
            replay_verification_id=(
                None if replay is None else replay.verification_id
            ),
        )


__all__ = [
    "DashboardSessionFinalRecoveryGateAuditRecoveryGate",
    "DashboardSessionFinalRecoveryGateAuditRecoveryReceipt",
]
