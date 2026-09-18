from __future__ import annotations

from dataclasses import replace

from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_chain_replay_verifier as chain_replay_model,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_chain import (
    DashboardSessionFinalRecoveryGateAuditChain,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_recovery_gate import (
    DashboardSessionFinalRecoveryGateAuditRecoveryGate,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_recovery_replay_verifier import (
    DashboardSessionFinalRecoveryGateAuditRecoveryReplayVerifier,
)


def _inputs():
    chain = DashboardSessionFinalRecoveryGateAuditChain(
        entries=(),
        chain_hash="0" * 64,
    )
    replay = chain_replay_model.DashboardSessionFinalRecoveryGateAuditChainReplayVerifier().verify(
        chain, chain
    )
    expected = DashboardSessionFinalRecoveryGateAuditRecoveryGate().evaluate(
        chain, replay, replay
    )
    return expected, chain, replay


def test_recovery_replay_matches() -> None:
    expected, chain, replay = _inputs()

    result = DashboardSessionFinalRecoveryGateAuditRecoveryReplayVerifier().verify(
        expected, chain, replay, replay
    )

    assert result.matches is True
    assert result.mismatches == ()
    assert result.expected_receipt_id == result.actual_receipt_id
    assert result.verification_id


def test_recovery_replay_reports_mismatch() -> None:
    expected, chain, replay = _inputs()
    altered = replace(expected, reason_code="ALTERED")

    result = DashboardSessionFinalRecoveryGateAuditRecoveryReplayVerifier().verify(
        altered, chain, replay, replay
    )

    assert result.matches is False
    assert result.mismatches == ("reason_code",)
