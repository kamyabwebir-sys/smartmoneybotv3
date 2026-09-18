from fastapi.testclient import TestClient

from api.main import create_app
from smart_money.adapters.persistence.live_capture_store import LiveCaptureStore
from smart_money.application.dashboard_runtime import (
    JsonAlertReviewStore,
    build_live_production_gate,
    build_subject_detail,
)


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


def test_dashboard_live_route_is_not_shadowed_by_parameterized_subject_route(tmp_path):
    """GET /dashboard/live must serve the page, not hit /dashboard/{subject_id}."""
    app = create_app(lifespan_enabled=False)
    with TestClient(app) as client:
        response = client.get("/dashboard/live")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "export-buttons" in response.text
        # The exact routes win, but the parameterized subject route still works.
        assert client.get("/dashboard/live", headers={"X-Probe": "1"}).status_code == 200


def test_h15_gate_rejects_unknown_safety_and_funding_status():
    """UNKNOWN must fail the gate: absent evidence is not evaluated evidence."""
    gate = build_live_production_gate(
        capture_available=True,
        data_fresh=True,
        report={"transaction_count": 1, "candidate_count": 1, "recovery_ok": True,
                "failures": [], "gate": {"passed": True},
                "ranking": [{"safety_status": "UNKNOWN", "funding_status": "UNKNOWN"}]},
    )
    assert gate["ready"] is False
    assert "safety_evaluated" in gate["failed_checks"]
    assert "funding_evaluated" in gate["failed_checks"]
    gate = build_live_production_gate(
        capture_available=True,
        data_fresh=True,
        report={"transaction_count": 1, "candidate_count": 1, "recovery_ok": True,
                "failures": [], "gate": {"passed": True},
                "ranking": [{"safety_status": "EVIDENCE_COMPLETE", "funding_status": "VERIFIED"}]},
    )
    assert gate["ready"] is True
    assert gate["failed_checks"] == []


def test_h15_gate_fails_closed_without_capture():
    """A missing/corrupt capture must fail every dependent check, not raise."""
    gate = build_live_production_gate(capture_available=False, data_fresh=False, report={})
    assert gate["ready"] is False
    assert gate["checks"]["capture_available"] is False
    assert gate["checks"]["data_fresh"] is False
    assert gate["checks"]["has_transactions"] is False
    assert gate["checks"]["safety_evaluated"] is False
    assert gate["fail_closed"] is True


def test_h15_gate_endpoint_fails_closed_on_unavailable_capture(tmp_path):
    """503-raising capture dir must yield a closed gate, not an error response."""
    app = create_app(lifespan_enabled=False)
    app.state.live_read_token = "secret"
    app.state.live_capture_dir = tmp_path / "does-not-exist"
    app.state.live_stale_after_seconds = 30
    with TestClient(app) as client:
        gate = client.get("/api/v1/live/gate", headers={"Authorization": "Bearer secret"})
        assert gate.status_code == 200
        document = gate.json()
        assert document["ready"] is False
        assert document["checks"]["capture_available"] is False
        assert document["checks"]["data_fresh"] is False
        assert document["failed_checks"].count("capture_available") == 1


def test_live_auth_fails_closed_when_not_configured(tmp_path):
    app = create_app(lifespan_enabled=False)
    app.state.live_read_token = None
    with TestClient(app) as client:
        assert client.get("/api/v1/live/overview", headers={"Authorization": "Bearer anything"}).status_code == 401


def test_h3_wallet_detail_aggregates_all_evidence_for_the_wallet(tmp_path, monkeypatch):
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
        assert client.get("/api/v1/live/wallets/wallet").status_code == 401
        detail = client.get("/api/v1/live/wallets/wallet", headers=headers)
        assert detail.status_code == 200
        document = detail.json()
        assert document["schema_version"] == "live_wallet_detail.v1"
        assert document["subject_kind"] == "wallet"
        assert document["summary"]["buy_count"] == 1
        assert document["summary"]["candidate_rows"] == 1
        assert document["summary"]["safety_statuses"] == ["EVIDENCE_COMPLETE"]
        assert document["observations"][0]["direction"] == "BUY"
        assert document["route_evidence"][0]["route"] == "raydium"
        assert client.get("/api/v1/live/wallets/nobody", headers=headers).status_code == 404


def test_h4_token_detail_aggregates_and_wallet_route_still_works(tmp_path, monkeypatch):
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
        detail = client.get("/api/v1/live/tokens/mint", headers=headers)
        assert detail.status_code == 200
        document = detail.json()
        assert document["schema_version"] == "live_token_detail.v1"
        assert document["subject_kind"] == "token"
        assert document["summary"]["candidate_rows"] == 1
        # Token detail carries no funding edges (edges are wallet-scoped).
        assert document["funding_edges"] == []
        assert client.get("/api/v1/live/tokens/unknown-mint", headers=headers).status_code == 404


def test_subject_detail_application_layer_is_testable_without_fastapi():
    report = {
        "ranking": [{"wallet": "w1", "mint": "m1", "score_bps": 7000, "safety_status": "EVIDENCE_COMPLETE", "funding_status": "VERIFIED", "signature": "sig-1"}],
        "normalized_observations": [{"wallet": "w1", "mint": "m1", "direction": "SELL", "slot": 5, "signature": "sig-1"}],
        "route_reports": [{"signature": "sig-1", "route": "orca"}],
        "swap_legs": [{"signature": "sig-1", "amount_in": 9}],
        "purchase_evaluations": [],
        "funding_graph_evidence": [{"source_wallet": "f", "target_wallet": "w1"}],
    }
    wallet = build_subject_detail(subject_kind="wallet", subject_id="w1", report=report)
    assert wallet["summary"] == {
        "activity_count": 1, "buy_count": 0, "sell_count": 1, "unknown_count": 0,
        "candidate_rows": 1, "max_score_bps": 7000,
        "safety_statuses": ["EVIDENCE_COMPLETE"], "funding_statuses": ["VERIFIED"],
    }
    assert wallet["swap_evidence"][0]["amount_in"] == 9
    assert wallet["funding_edges"][0]["target_wallet"] == "w1"
    token = build_subject_detail(subject_kind="token", subject_id="m1", report=report)
    assert token["summary"]["sell_count"] == 1
    assert token["funding_edges"] == []
    for kind, missing in (("wallet", "w2"), ("token", "m2"), ("wallet", "  "), ("mint", "m1")):
        with __import__("pytest").raises(ValueError):
            build_subject_detail(subject_kind=kind, subject_id=missing, report=report)


def test_playtest_end_to_end_download_path_matches_ui_contract(tmp_path, monkeypatch):
    """Replay of the live-server playtest: the exact requests dashboard.js's
    downloadExport and loadGate make must produce decodable, batch-faithful
    payloads and a renderable gate status."""
    capture = tmp_path / "capture"
    store = LiveCaptureStore(capture, "playtest-wallet", "mainnet-beta", clock=lambda: 1000)
    store.page(lambda *args: {"result": [{"signature": "sig-a"}]}, "playtest-wallet", 1)
    store.transaction(lambda sig: {"result": {"transaction": {"signatures": [sig]}}}, "sig-a")
    batch = {"signature_count": 1, "transaction_count": 1, "candidate_count": 1,
             "ranking": [{"evidence_id": "cand-1", "wallet": "playtest-wallet", "mint": "mint-x",
                          "score_bps": 8100, "safety_status": "EVIDENCE_COMPLETE", "funding_status": "VERIFIED"}],
             "route_reports": [], "swap_legs": [], "funding_graph_evidence": [],
             "failures": [], "recovery_ok": True, "gate": {"passed": True}}
    store.complete(batch)
    store.close()
    monkeypatch.setattr("api.routes.live.time.time", lambda: 1010)
    app = create_app(lifespan_enabled=False)
    app.state.live_read_token = "secret"
    app.state.live_capture_dir = capture
    app.state.live_stale_after_seconds = 3600
    app.state.live_review_store = JsonAlertReviewStore(tmp_path / "reviews.json")
    app.state.live_quality_dataset = __import__("pathlib").Path("fixtures/quality/independent-evaluation-v1.json")
    with TestClient(app) as client:
        # The dashboard page itself must be servable (route-ordering regression guard).
        page = client.get("/dashboard/live")
        assert page.status_code == 200 and "export-buttons" in page.text
        headers = {"Authorization": "Bearer secret"}

        # downloadExport JSON path: decodable, batch-faithful, attachment-flagged.
        response = client.get("/api/v1/live/export/candidates", headers=headers)
        assert response.status_code == 200
        assert "attachment" in response.headers["content-disposition"]
        document = response.json()
        assert document["schema_version"] == "live_dashboard_export.v1"
        assert document["items"] == batch["ranking"]

        # downloadExport CSV path: BOM-prefixed, decodable, correct columns.
        response = client.get("/api/v1/live/export/candidates?format=csv", headers=headers)
        assert response.status_code == 200
        assert response.content[:3] == b"\xef\xbb\xbf"
        decoded = response.content.decode("utf-8-sig")
        assert decoded.splitlines()[0].startswith("evidence_id")
        assert "cand-1" in decoded

        # loadGate path: gate renders READY for a healthy batch.
        gate = client.get("/api/v1/live/gate", headers=headers).json()
        assert gate["ready"] is True
        assert gate["failed_checks"] == []
        assert gate["fail_closed"] is True
