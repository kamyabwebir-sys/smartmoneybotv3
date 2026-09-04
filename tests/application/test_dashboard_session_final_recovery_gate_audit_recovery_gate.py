from __future__ import annotations

from dataclasses import replace

from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_chain_replay_verifier as replay_model,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_chain import (
    DashboardSessionFinalRecoveryGateAuditChain,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_recovery_gate import (
    DashboardSessionFinalRecoveryGateAuditRecoveryGate,
)


def _inputs():
    chain = DashboardSessionFinalRecoveryGateAuditChain(
        entries=(),
        chain_hash="0" * 64,
    )
    replay = replay_model.DashboardSessionFinalRecoveryGateAuditChainReplayVerifier().verify(
        chain, chain
    )
    return chain, replay


def test_gate_returns_ready_for_verified_persisted_replay() -> None:
    chain, replay = _inputs()

    result = DashboardSessionFinalRecoveryGateAuditRecoveryGate().evaluate(
        chain, replay, replay
    )

    assert result.decision == "READY"
    assert result.reason_code == "GATE_AUDIT_CHAIN_RECOVERY_VERIFIED"
    assert result.chain_id == chain.chain_id


def test_gate_fails_closed_on_persisted_mismatch() -> None:
    chain, replay = _inputs()
    altered = replace(replay, actual_chain_id="different")

    result = DashboardSessionFinalRecoveryGateAuditRecoveryGate().evaluate(
        chain, replay, altered
    )

    assert result.decision == "BLOCKED"
    assert result.reason_code == "PERSISTED_GATE_AUDIT_REPLAY_MISMATCH"
