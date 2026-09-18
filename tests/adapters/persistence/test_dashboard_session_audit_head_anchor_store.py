import pytest

from smart_money.adapters.persistence.dashboard_session_audit_head_anchor_store import (
    JsonDashboardSessionAuditHeadAnchorStore,
)
from smart_money.application.dashboard_session_audit_head_anchor import (
    DashboardSessionAuditHeadAnchor,
)
from tests.application.test_dashboard_session_audit_head_anchor import _chain


def test_session_head_anchor_store_is_atomic_and_reloadable(tmp_path) -> None:
    path = tmp_path / "session-head.json"
    anchor = DashboardSessionAuditHeadAnchor.from_chain(_chain())
    store = JsonDashboardSessionAuditHeadAnchorStore(path)

    assert store.save(anchor) == anchor.anchor_id
    assert JsonDashboardSessionAuditHeadAnchorStore(path).load() == anchor


def test_session_head_anchor_store_rejects_corruption(tmp_path) -> None:
    path = tmp_path / "session-head.json"
    store = JsonDashboardSessionAuditHeadAnchorStore(path)
    store.save(DashboardSessionAuditHeadAnchor.from_chain(_chain()))
    path.write_text(path.read_text(encoding="utf-8") + "x", encoding="utf-8")

    with pytest.raises(ValueError):
        JsonDashboardSessionAuditHeadAnchorStore(path)
