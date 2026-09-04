from __future__ import annotations

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
from smart_money.application.dashboard_session_recovery_gate import (
    DashboardSessionRecoveryGate,
)
from smart_money.application.dashboard_session_recovery_replay_verifier import (
    DashboardSessionRecoveryReplayVerifier,
)


def _chain() -> DashboardSessionFinalAuditChain:
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
    return DashboardSessionFinalAuditChain.from_chain(
        source, final, final_replay
    )


def test_chain_replay_matches() -> None:
    chain = _chain()

    result = DashboardSessionFinalAuditChainReplayVerifier().verify(
        chain, chain
    )

    assert result.matches is True
    assert result.mismatches == ()
    assert result.expected_chain_id == result.actual_chain_id
    assert result.verification_id


def test_chain_replay_reports_hash_mismatch() -> None:
    chain = _chain()
    altered = DashboardSessionFinalAuditChain(
        entries=(),
        chain_hash="0" * 64,
    )

    result = DashboardSessionFinalAuditChainReplayVerifier().verify(
        chain, altered
    )

    assert result.matches is False
    assert "chain_id" in result.mismatches
    assert "chain_hash" in result.mismatches
    assert "entry_count" in result.mismatches
