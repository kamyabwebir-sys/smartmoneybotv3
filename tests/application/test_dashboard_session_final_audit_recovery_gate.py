from __future__ import annotations

from dataclasses import replace

from smart_money.application.dashboard_session_audit_chain import (
    DashboardSessionAuditChain,
)
from smart_money.application.dashboard_session_audit_final_replay_verifier import (
    DashboardSessionAuditFinalReplayVerifier,
)
from smart_money.application.dashboard_session_audit_finalizer import (
    DashboardSessionAuditChainFinalizer,
)
from smart_money.application.dashboard_session_audit_head_anchor import (
    DashboardSessionAuditHeadAnchor,
)
from smart_money.application.dashboard_session_final_audit_chain import (
    DashboardSessionFinalAuditChain,
)
from smart_money.application.dashboard_session_final_audit_chain_replay_verifier import (
    DashboardSessionFinalAuditChainReplayVerifier,
)
from smart_money.application.dashboard_session_final_audit_recovery_gate import (
    DashboardSessionFinalAuditRecoveryGate,
)
from smart_money.application.dashboard_session_recovery_gate import (
    DashboardSessionRecoveryGate,
)
from smart_money.application.dashboard_session_recovery_replay_verifier import (
    DashboardSessionRecoveryReplayVerifier,
)


def _inputs():
    source = DashboardSessionAuditChain(entries=(), chain_hash="0" * 64)
    anchor = DashboardSessionAuditHeadAnchor.from_chain(source)
    recovery = DashboardSessionRecoveryGate().evaluate(source, anchor)
    recovery_replay = DashboardSessionRecoveryReplayVerifier().verify(
        source, anchor, recovery
    )
    final = DashboardSessionAuditChainFinalizer().finalize(
        source, anchor, recovery, recovery_replay
    )
    final_replay = DashboardSessionAuditFinalReplayVerifier().verify(
        final, source, anchor, recovery, recovery_replay
    )
    chain = DashboardSessionFinalAuditChain.from_chain(
        source, final, final_replay
    )
    replay = DashboardSessionFinalAuditChainReplayVerifier().verify(
        chain, chain
    )
    return chain, replay


def test_recovery_gate_returns_ready_for_verified_persisted_replay() -> None:
    chain, replay = _inputs()

    result = DashboardSessionFinalAuditRecoveryGate().evaluate(
        chain, replay, replay
    )

    assert result.decision == "READY"
    assert result.reason_code == "FINAL_AUDIT_CHAIN_RECOVERY_VERIFIED"
    assert result.chain_id == chain.chain_id
    assert result.replay_verification_id == replay.verification_id


def test_recovery_gate_fails_closed_on_persisted_mismatch() -> None:
    chain, replay = _inputs()
    altered = replace(replay, actual_chain_id="different")

    result = DashboardSessionFinalAuditRecoveryGate().evaluate(
        chain, replay, altered
    )

    assert result.decision == "BLOCKED"
    assert result.reason_code == "PERSISTED_FINAL_AUDIT_REPLAY_MISMATCH"


def test_recovery_gate_fails_closed_when_replay_is_missing() -> None:
    chain, _ = _inputs()

    result = DashboardSessionFinalAuditRecoveryGate().evaluate(
        chain, None, None
    )

    assert result.decision == "BLOCKED"
    assert result.reason_code == "MISSING_FINAL_AUDIT_CHAIN_OR_REPLAY"
