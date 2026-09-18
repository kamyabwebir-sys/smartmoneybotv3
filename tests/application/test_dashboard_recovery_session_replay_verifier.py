from smart_money.application.dashboard_audit_recovery_gate import (
    DashboardAuditRecoveryReceipt,
)
from smart_money.application.dashboard_macro_read_index import (
    DashboardMacroReadIndex,
)
from smart_money.application.dashboard_query_endpoint import (
    DashboardQueryEndpoint,
)
from smart_money.application.dashboard_recovery_query_session import (
    DashboardRecoveryQuerySession,
)
from smart_money.application.dashboard_recovery_session_replay_verifier import (
    DashboardRecoverySessionReplayVerifier,
)
from smart_money.application.dashboard_subject_detail_query import (
    DashboardSubjectDetailQuery,
)


def test_session_replay_verifier_blocks_and_matches_without_data_source() -> None:
    session = DashboardRecoveryQuerySession(
        DashboardQueryEndpoint(DashboardMacroReadIndex.from_responses([]))
    )
    recovery = DashboardAuditRecoveryReceipt(
        decision="BLOCKED",
        reason_code="CHAIN_HEAD_MISMATCH",
        anchor_id="anchor",
        chain_id="chain",
    )
    query = DashboardSubjectDetailQuery(query="replay")
    _, _, expected = session.execute(recovery, query)

    verification = DashboardRecoverySessionReplayVerifier(session).verify(
        recovery,
        query,
        expected,
    )

    assert verification.matches is True
    assert verification.mismatches == ()


def test_session_replay_verifier_detects_recovery_drift() -> None:
    session = DashboardRecoveryQuerySession(
        DashboardQueryEndpoint(DashboardMacroReadIndex.from_responses([]))
    )
    expected_recovery = DashboardAuditRecoveryReceipt(
        decision="READY",
        reason_code="CHAIN_HEAD_VERIFIED",
        anchor_id="anchor",
        chain_id="chain",
    )
    query = DashboardSubjectDetailQuery(query="replay")
    _, _, expected = session.execute(expected_recovery, query)
    changed_recovery = DashboardAuditRecoveryReceipt(
        decision="BLOCKED",
        reason_code="CHAIN_HEAD_MISMATCH",
        anchor_id="anchor",
        chain_id="chain",
    )

    verification = DashboardRecoverySessionReplayVerifier(session).verify(
        changed_recovery,
        query,
        expected,
    )

    assert verification.matches is False
    assert "session_status" in verification.mismatches
