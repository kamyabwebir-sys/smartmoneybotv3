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
from smart_money.application.dashboard_session_audit_head_anchor import (
    DashboardSessionAuditHeadAnchor,
)


def _chain() -> DashboardSessionAuditChain:
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
    return DashboardSessionAuditChain.from_receipts(
        recovery, query, session, replay
    )


def test_session_head_anchor_matches_chain() -> None:
    chain = _chain()
    anchor = DashboardSessionAuditHeadAnchor.from_chain(chain)

    assert anchor.matches(chain) is True
    assert anchor.entry_count == 4
    assert anchor.latest_entry_kind == "replay"
    assert anchor.latest_entry_id == chain.entries[-1].entry_id
    assert anchor.anchor_id == DashboardSessionAuditHeadAnchor.from_chain(
        chain
    ).anchor_id
