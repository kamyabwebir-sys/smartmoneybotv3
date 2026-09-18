from smart_money.adapters.persistence.dashboard_query_audit_chain_store import (
    JsonDashboardQueryAuditChainStore,
)
from smart_money.application.dashboard_query_audit_chain import (
    DashboardQueryAuditChain,
)
from smart_money.application.dashboard_query_replay_verifier import (
    DashboardQueryReplayReceipt,
)


def _chain() -> DashboardQueryAuditChain:
    receipts = tuple(
        DashboardQueryReplayReceipt(
            query_id=f"query-{index}",
            expected_receipt_id=f"expected-{index}",
            actual_receipt_id=f"actual-{index}",
            matches=True,
        )
        for index in (1, 2)
    )
    return DashboardQueryAuditChain.from_receipts(receipts)


def test_chain_store_is_atomic_and_reloads(tmp_path) -> None:
    path = tmp_path / "audit-chain.json"
    chain = _chain()
    store = JsonDashboardQueryAuditChainStore(path)

    assert store.save(chain) == chain.chain_id
    reloaded = JsonDashboardQueryAuditChainStore(path)

    assert reloaded.load() == chain
    assert reloaded.chain_id == chain.chain_id


def test_chain_store_rejects_drift(tmp_path) -> None:
    path = tmp_path / "audit-chain.json"
    store = JsonDashboardQueryAuditChainStore(path)
    store.save(_chain())
    path.write_text(path.read_text(encoding="utf-8").replace(
        '"chain_hash":"', '"chain_hash":"0'
    ), encoding="utf-8")

    try:
        JsonDashboardQueryAuditChainStore(path)
    except ValueError:
        pass
    else:
        raise AssertionError("drifted audit chain was accepted")
