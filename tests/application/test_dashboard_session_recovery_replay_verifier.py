from smart_money.application.dashboard_session_audit_chain import (
    DashboardSessionAuditChain,
)
from smart_money.application.dashboard_session_audit_head_anchor import (
    DashboardSessionAuditHeadAnchor,
)
from smart_money.application.dashboard_session_recovery_gate import (
    DashboardSessionRecoveryGate,
)
from smart_money.application.dashboard_session_recovery_replay_verifier import (
    DashboardSessionRecoveryReplayVerifier,
)


def test_session_recovery_replay_matches() -> None:
    chain = DashboardSessionAuditChain(entries=(), chain_hash="0" * 64)
    anchor = DashboardSessionAuditHeadAnchor.from_chain(chain)
    expected = DashboardSessionRecoveryGate().evaluate(chain, anchor)

    verification = DashboardSessionRecoveryReplayVerifier().verify(
        chain, anchor, expected
    )

    assert verification.matches is True
    assert verification.mismatches == ()


def test_session_recovery_replay_detects_head_drift() -> None:
    chain = DashboardSessionAuditChain(entries=(), chain_hash="0" * 64)
    anchor = DashboardSessionAuditHeadAnchor.from_chain(chain)
    expected = DashboardSessionRecoveryGate().evaluate(chain, anchor)
    changed = DashboardSessionAuditHeadAnchor(
        chain_id="other",
        chain_hash="b" * 64,
        entry_count=0,
        latest_entry_id=None,
        latest_entry_kind=None,
    )

    verification = DashboardSessionRecoveryReplayVerifier().verify(
        chain, changed, expected
    )

    assert verification.matches is False
    assert "decision" in verification.mismatches
