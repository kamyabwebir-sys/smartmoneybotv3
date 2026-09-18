from smart_money.application.dashboard_audit_recovery_gate import (
    DashboardAuditRecoveryReceipt,
)
from smart_money.application.dashboard_query_audit_receipt import (
    DashboardQueryAuditReceipt,
)
from smart_money.application.dashboard_recovery_query_session import (
    DashboardRecoveryQuerySessionReceipt,
)
from smart_money.application.dashboard_recovery_session_replay_verifier import (
    DashboardSessionReplayReceipt,
)
from smart_money.application.dashboard_session_audit_chain import (
    DashboardSessionAuditChain,
)


def test_session_audit_chain_preserves_canonical_parent_order() -> None:
    recovery = DashboardAuditRecoveryReceipt(
        "READY", "CHAIN_HEAD_VERIFIED", "anchor", "chain"
    )
    query = DashboardQueryAuditReceipt(
        "query", "SUCCESS", "result", "result", "a" * 64, 1, ("q.v1",)
    )
    session = DashboardRecoveryQuerySessionReceipt(
        "EXECUTED", recovery.receipt_id, "query", query.receipt_id, "RECOVERY_GATE_READY"
    )
    replay = DashboardSessionReplayReceipt(
        session.session_id, session.session_id, True
    )

    chain = DashboardSessionAuditChain.from_receipts(
        recovery, query, session, replay
    )

    assert [entry.parent_id for entry in chain.entries] == [
        None,
        recovery.receipt_id,
        query.receipt_id,
        session.session_id,
    ]
    assert chain.chain_id == DashboardSessionAuditChain.from_receipts(
        recovery, query, session, replay
    ).chain_id
