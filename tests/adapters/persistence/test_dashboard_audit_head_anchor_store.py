import pytest

from smart_money.adapters.persistence.dashboard_audit_head_anchor_store import (
    JsonDashboardAuditHeadAnchorStore,
)
from smart_money.application.dashboard_audit_head_anchor import (
    DashboardAuditHeadAnchor,
)
from smart_money.application.dashboard_query_audit_chain import (
    DashboardQueryAuditChain,
)
from smart_money.application.dashboard_query_replay_verifier import (
    DashboardQueryReplayReceipt,
)


def _anchor() -> DashboardAuditHeadAnchor:
    receipt = DashboardQueryReplayReceipt(
        query_id="q",
        expected_receipt_id="e",
        actual_receipt_id="a",
        matches=True,
    )
    return DashboardAuditHeadAnchor.from_chain(
        DashboardQueryAuditChain.from_receipts([receipt])
    )


def test_anchor_store_is_atomic_and_idempotent(tmp_path) -> None:
    path = tmp_path / "head.json"
    anchor = _anchor()
    store = JsonDashboardAuditHeadAnchorStore(path)

    assert store.save(anchor) == anchor.anchor_id
    assert store.save(anchor) == anchor.anchor_id
    assert JsonDashboardAuditHeadAnchorStore(path).load() == anchor


def test_anchor_store_rejects_rollback_and_corruption(tmp_path) -> None:
    path = tmp_path / "head.json"
    store = JsonDashboardAuditHeadAnchorStore(path)
    anchor = _anchor()
    store.save(anchor)
    with pytest.raises(RuntimeError, match="rollback"):
        store.save(DashboardAuditHeadAnchor(
            chain_id="other",
            chain_hash="b" * 64,
            receipt_count=0,
            latest_verification_id=None,
        ))
    path.write_text(path.read_text(encoding="utf-8") + "x", encoding="utf-8")
    with pytest.raises(ValueError):
        JsonDashboardAuditHeadAnchorStore(path)
