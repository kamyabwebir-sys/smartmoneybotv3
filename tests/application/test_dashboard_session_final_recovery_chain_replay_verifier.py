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
from smart_money.application.dashboard_session_final_recovery_audit_chain import (
    DashboardSessionFinalRecoveryAuditChain,
)
from smart_money.application.dashboard_session_final_recovery_audit_chain_replay_verifier import (
    DashboardSessionFinalRecoveryAuditChainReplayVerifier,
)
from smart_money.application.dashboard_session_final_recovery_chain_gate import (
    DashboardSessionFinalRecoveryChainGate,
)
from smart_money.application.dashboard_session_final_recovery_chain_replay_verifier import (
    DashboardSessionFinalRecoveryChainReplayVerifier,
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
    final_chain = DashboardSessionFinalAuditChain.from_chain(
        source, final, final_replay
    )
    final_chain_replay = DashboardSessionFinalAuditChainReplayVerifier().verify(
        final_chain, final_chain
    )
    final_recovery = DashboardSessionFinalAuditRecoveryGate().evaluate(
        final_chain, final_chain_replay, final_chain_replay
    )
    final_recovery_replay = (
        DashboardSessionFinalAuditRecoveryReplayVerifier().verify(
            final_recovery,
            final_chain,
            final_chain_replay,
            final_chain_replay,
        )
    )
    chain = DashboardSessionFinalRecoveryAuditChain.from_chain(
        final_chain, final_recovery, final_recovery_replay
    )
    chain_replay = DashboardSessionFinalRecoveryAuditChainReplayVerifier().verify(
        chain, chain
    )
    expected = DashboardSessionFinalRecoveryChainGate().evaluate(
        chain, chain_replay, chain_replay
    )
    return expected, chain, chain_replay


def test_gate_replay_matches() -> None:
    expected, chain, replay = _inputs()

    result = DashboardSessionFinalRecoveryChainReplayVerifier().verify(
        expected, chain, replay, replay
    )

    assert result.matches is True
    assert result.mismatches == ()
    assert result.expected_receipt_id == result.actual_receipt_id
    assert result.verification_id


def test_gate_replay_reports_mismatch() -> None:
    expected, chain, replay = _inputs()
    altered = replace(expected, reason_code="ALTERED")

    result = DashboardSessionFinalRecoveryChainReplayVerifier().verify(
        altered, chain, replay, replay
    )

    assert result.matches is False
    assert result.mismatches == ("reason_code",)
