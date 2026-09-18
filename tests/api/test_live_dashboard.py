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


def test_h14_export_json_and_csv_are_authenticated_and_deterministic(tmp_path, monkeypatch):
    capture = tmp_path / "capture"
    _build_capture(capture)
    monkeypatch.setattr("api.routes.live.time.time", lambda: 1010)
    app = create_app(lifespan_enabled=False)
    app.state.live_read_token = "secret"
    app.state.live_capture_dir = capture
    app.state.live_stale_after_seconds = 30
    app.state.live_review_store = JsonAlertReviewStore(tmp_path / "reviews.json")
    app.state.live_quality_dataset = __import__("pathlib").Path("fixtures/quality/independent-evaluation-v1.json")
    headers = {"Authorization": "Bearer secret"}
    with TestClient(app) as client:
        assert client.get("/api/v1/live/export/candidates").status_code == 401
        data = client.get("/api/v1/live/export/candidates", headers=headers)
        assert data.status_code == 200
        assert data.headers["content-type"].startswith("application/json")
        assert "attachment" in data.headers["content-disposition"]
        document = data.json()
        assert document["schema_version"] == "live_dashboard_export.v1"
        assert document["table"] == "candidates"
        assert document["read_only"] is True
        assert len(document["items"]) == 1
        assert document["items"][0]["evidence_id"] == "candidate-1"
        # JSON export must be deterministic (sorted keys, stable identity).
        again = client.get("/api/v1/live/export/candidates", headers=headers)
        assert again.json()["items"] == document["items"]

        csv_data = client.get("/api/v1/live/export/candidates?format=csv", headers=headers)
        assert csv_data.status_code == 200
        assert csv_data.headers["content-type"].startswith("text/csv")
        text = csv_data.content.decode("utf-8-sig")
        lines = text.strip().splitlines()
        assert lines[0].startswith("evidence_id")
        assert "candidate-1" in lines[1]

        observations = client.get("/api/v1/live/export/observations?format=csv", headers=headers)
        assert observations.status_code == 200
        assert "BUY" in observations.content.decode("utf-8-sig")

        assert client.get("/api/v1/live/export/unknown-table", headers=headers).status_code == 422
        assert client.get("/api/v1/live/export/candidates?format=xml", headers=headers).status_code == 422


def test_h15_production_gate_fails_closed_and_reports_failed_checks(tmp_path, monkeypatch):
    capture = tmp_path / "capture"
    _build_capture(capture)
    monkeypatch.setattr("api.routes.live.time.time", lambda: 1010)
    app = create_app(lifespan_enabled=False)
    app.state.live_read_token = "secret"
    app.state.live_capture_dir = capture
    app.state.live_stale_after_seconds = 30
    app.state.live_review_store = JsonAlertReviewStore(tmp_path / "reviews.json")
    app.state.live_quality_dataset = __import__("pathlib").Path("fixtures/quality/independent-evaluation-v1.json")
    headers = {"Authorization": "Bearer secret"}
    with TestClient(app) as client:
        assert client.get("/api/v1/live/gate").status_code == 401
        gate = client.get("/api/v1/live/gate", headers=headers)
        assert gate.status_code == 200
        document = gate.json()
        assert document["schema_version"] == "live_dashboard_production_gate.v1"
        assert document["fail_closed"] is True
        assert document["read_only"] is True
        # The fixture batch gate is false, so the gate must NOT be ready.
        assert document["ready"] is False
        assert "batch_gate_passed" in document["failed_checks"]
        assert set(document["checks"]) == {
            "capture_available", "data_fresh", "has_transactions", "has_candidates",
            "recovery_ok", "no_unresolved_failures", "safety_evaluated",
            "funding_evaluated", "batch_gate_passed",
        }
        # Checks that must genuinely pass on this healthy fixture.
        assert document["checks"]["capture_available"] is True
        assert document["checks"]["data_fresh"] is True
        assert document["checks"]["has_transactions"] is True
        assert document["checks"]["has_candidates"] is True
        assert document["checks"]["safety_evaluated"] is True
        assert document["checks"]["funding_evaluated"] is True
        assert client.get("/api/v1/live/gate", headers={"Authorization": "Bearer wrong"}).status_code == 401


def test_live_auth_fails_closed_when_not_configured(tmp_path):
    app = create_app(lifespan_enabled=False)
    app.state.live_read_token = None
    with TestClient(app) as client:
        assert client.get("/api/v1/live/overview", headers={"Authorization": "Bearer anything"}).status_code == 401
