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
from smart_money.application.dashboard_session_final_audit_recovery_replay_verifier import (
    DashboardSessionFinalAuditRecoveryReplayVerifier,
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
    expected = DashboardSessionFinalAuditRecoveryGate().evaluate(
        chain, replay, replay
    )
    return expected, chain, replay


def test_recovery_replay_matches() -> None:
    expected, chain, replay = _inputs()

    result = DashboardSessionFinalAuditRecoveryReplayVerifier().verify(
        expected, chain, replay, replay
    )

    assert result.matches is True
    assert result.mismatches == ()
    assert result.expected_receipt_id == result.actual_receipt_id
    assert result.verification_id


def test_recovery_replay_reports_mismatch() -> None:
    expected, chain, replay = _inputs()
    altered = replace(expected, reason_code="ALTERED")

    result = DashboardSessionFinalAuditRecoveryReplayVerifier().verify(
        altered, chain, replay, replay
    )

    assert result.matches is False
    assert result.mismatches == ("reason_code",)
