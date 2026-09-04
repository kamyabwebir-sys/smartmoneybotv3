import pytest

from smart_money.adapters.persistence.dashboard_session_audit_chain_store import (
    JsonDashboardSessionAuditChainStore,
)
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
    replay = DashboardSessionReplayReceipt(session.session_id, session.session_id, True)
    return DashboardSessionAuditChain.from_receipts(
        recovery, query, session, replay
    )


def test_store_is_atomic_and_reloadable(tmp_path) -> None:
    path = tmp_path / "session-chain.json"
    chain = _chain()
    store = JsonDashboardSessionAuditChainStore(path)

    assert store.save(chain) == chain.chain_id
    assert JsonDashboardSessionAuditChainStore(path).load() == chain


def test_store_rejects_overwrite_and_corruption(tmp_path) -> None:
    path = tmp_path / "session-chain.json"
    store = JsonDashboardSessionAuditChainStore(path)
    chain = _chain()
    store.save(chain)
    with pytest.raises(RuntimeError):
        store.save(DashboardSessionAuditChain.from_receipts(
            DashboardAuditRecoveryReceipt(
                "BLOCKED", "MISSING_CHAIN_OR_ANCHOR", None, None
            ),
            DashboardQueryAuditReceipt(
                "query", "EMPTY", "result", "result", "b" * 64, 0, ("q.v1",)
            ),
            DashboardRecoveryQuerySessionReceipt(
                "BLOCKED", "recovery", "query", None, "RECOVERY_GATE_BLOCKED"
            ),
            DashboardSessionReplayReceipt("s", "s", True),
        ))
    path.write_text(path.read_text(encoding="utf-8") + "x", encoding="utf-8")
    with pytest.raises(ValueError):
        JsonDashboardSessionAuditChainStore(path)
