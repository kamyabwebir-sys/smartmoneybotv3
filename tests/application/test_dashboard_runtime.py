from smart_money.application.dashboard_runtime import (
    AlertReviewRecord,
    DashboardCache,
    DashboardOperationalGate,
    JsonAlertReviewStore,
)
from smart_money.core.ids import deterministic_id


def test_cache_and_operational_gate_are_deterministic():
    cache = DashboardCache()
    cache.put("overview", "h1", {"count": 1})
    assert cache.get("overview", "h1") == {"count": 1}
    assert cache.get("overview", "h2") is None
    gate = DashboardOperationalGate.evaluate({"api": True, "replay": True})
    assert gate.ready


def test_alert_review_store_round_trip(tmp_path):
    identity = {"alert_id": "a1", "status": "ACCEPTED", "reviewer": "operator"}
    record = AlertReviewRecord("a1", "ACCEPTED", "operator", deterministic_id("dashboard_alert_review", identity))
    store = JsonAlertReviewStore(tmp_path / "alerts.json")
    assert store.save(record) == record.review_id
    assert JsonAlertReviewStore(tmp_path / "alerts.json").get(record.review_id) == record
