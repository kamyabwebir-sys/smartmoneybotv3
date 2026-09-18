from fastapi.testclient import TestClient

from api.main import create_app
from smart_money.adapters.persistence.live_capture_store import LiveCaptureStore
from smart_money.application.dashboard_runtime import JsonAlertReviewStore


def _build_capture(path):
    store = LiveCaptureStore(path, "wallet", "mainnet-beta", clock=lambda: 1000)
    store.page(lambda *args: {"result": [{"signature": "sig"}]}, "wallet", 1)
    store.transaction(lambda sig: {"result": {"transaction": {"signatures": [sig]}}}, "sig")
    result = {"signature_count": 1, "transaction_count": 1, "candidate_count": 1,
              "ranking": [{"evidence_id": "candidate-1", "wallet": "wallet", "mint": "mint", "score_bps": 8000, "signature": "sig",
                           "safety_status": "EVIDENCE_COMPLETE", "safety_evidence": {"mint_authority": None, "top_accounts_concentration_bps": 2500},
                           "funding_status": "VERIFIED", "funding_edge_ids": ["edge-1"], "funding_evidence": [{"evidence_id": "edge-1"}]}],
              "funding_graph_evidence": [{"evidence_id": "edge-1"}],
              "route_reports": [{"signature": "sig", "route": "raydium"}],
              "swap_legs": [{"signature": "sig", "amount": 4}],
              "purchase_evaluations": [{"signature": "sig", "eligible": True}], "failures": [],
              "normalized_observations": [{"signature": "sig", "slot": 10, "wallet": "wallet", "direction": "BUY", "observation_id": "obs", "evidence_id": "ev", "duplicate": False}],
              "gate": {"passed": False}}
    store.complete(result)
    store.close()


def test_live_dashboard_is_authenticated_fresh_and_reviewable(tmp_path, monkeypatch):
    capture = tmp_path / "capture"
    _build_capture(capture)
    monkeypatch.setattr("api.routes.live.time.time", lambda: 1010)
    app = create_app(lifespan_enabled=False)
    app.state.live_read_token = "secret"
    app.state.live_capture_dir = capture
    app.state.live_stale_after_seconds = 30
    app.state.live_review_store = JsonAlertReviewStore(tmp_path / "reviews.json")
    app.state.live_quality_dataset = __import__("pathlib").Path("fixtures/quality/independent-evaluation-v1.json")
    with TestClient(app) as client:
        assert client.get("/api/v1/live/overview").status_code == 401
        headers = {"Authorization": "Bearer secret"}
        overview = client.get("/api/v1/live/overview", headers=headers)
        assert overview.status_code == 200
        assert overview.json()["freshness"] == {"captured_at_epoch": 1000, "age_seconds": 10, "stale": False}
        detail = client.get("/api/v1/live/candidates/candidate-1", headers=headers).json()
        assert detail["route_evidence"][0]["route"] == "raydium"
        assert detail["candidate"]["safety_status"] == "EVIDENCE_COMPLETE"
        assert detail["funding_graph"]["edge_ids"] == ["edge-1"]
        assert detail["safety_report"]["fail_closed"] is False
        assert client.get("/api/v1/live/candidates/candidate-1/funding", headers=headers).json()["status"] == "VERIFIED"
        assert client.get("/api/v1/live/candidates/candidate-1/safety", headers=headers).json()["status"] == "EVIDENCE_COMPLETE"
        assert client.get("/api/v1/live/quality", headers=headers).json()["precision_bps"] == 6666
        observations = client.get("/api/v1/live/observations", headers=headers).json()
        assert observations["total"] == 1
        assert observations["items"][0]["direction"] == "BUY"
        report = client.get("/api/v1/live/reports/fa", headers=headers).json()
        assert report["metrics"]["buy_count"] == 1
        assert report["read_only"] is True
        assert client.get("/dashboard/assets/dashboard.js").status_code == 200
        review = client.post("/api/v1/live/reviews", headers=headers, json={"candidate_id": "candidate-1", "status": "ACCEPTED", "reviewer": "operator"})
        assert review.status_code == 201 and review.json()["status"] == "ACCEPTED"
        assert client.post("/api/v1/live/reviews", headers=headers, json={"candidate_id": "candidate-1", "status": "PROPOSED", "reviewer": "operator"}).status_code == 422
        assert client.post("/api/v1/live/reviews", headers=headers, json={"candidate_id": "missing", "status": "ACCEPTED", "reviewer": "operator"}).status_code == 422


def test_live_auth_fails_closed_when_not_configured(tmp_path):
    app = create_app(lifespan_enabled=False)
    app.state.live_read_token = None
    with TestClient(app) as client:
        assert client.get("/api/v1/live/overview", headers={"Authorization": "Bearer anything"}).status_code == 401
