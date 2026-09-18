import json
from copy import deepcopy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from smart_money.adapters.persistence.wallet_route_fixture import EVIDENCE_ID, WALLET, replay_route_fixture
from smart_money.application.wallet_route_evidence import project_wallet_route
from smart_money.application.solana_candidate_pipeline import rank_wallet_token_candidates

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures/solana/mainnet/s12-cycle.json"


def raw():
    return json.loads(FIXTURE.read_bytes())["result"]


def test_mainnet_replay_and_exclusion():
    replay = replay_route_fixture(FIXTURE)
    report = replay["report"]
    assert report["evidence_id"] == EVIDENCE_ID
    assert report["native_delta_excluding_fee"] == 0
    assert len(report["transfers"]) == 9
    assert [r["classification"] for r in report["items"]] == ["INTERMEDIATE", "ROUND_TRIP_FLOW"]
    assert [r["raw_delta"] for r in report["items"]] == ["0", "35068942933"]
    assert all(not row["ranking_eligible"] for row in replay["ranking"])
    assert not report["cycle_verified"]


def test_order_independent_balances_and_no_mutation():
    tx = raw()
    before = deepcopy(tx)
    first = project_wallet_route(tx, WALLET)
    assert tx == before
    tx["meta"]["preTokenBalances"].reverse()
    assert project_wallet_route(tx, WALLET) == first


def test_missing_inner_instructions_fails_closed():
    tx = raw()
    tx["meta"]["innerInstructions"] = None
    report = project_wallet_route(tx, WALLET)
    assert report["gaps"]
    assert all(i["classification"] == "UNKNOWN" for i in report["items"])


def test_transfer_amount_tampering_cannot_be_ranked():
    tx = raw()
    tx["meta"]["innerInstructions"][0]["instructions"][0]["parsed"]["info"]["tokenAmount"]["amount"] = "1"
    report = project_wallet_route(tx, WALLET)
    assert report["gaps"]
    assert all(not i["ranking_eligible"] for i in report["items"])


def test_fixture_tamper(tmp_path):
    path = tmp_path / "bad.json"
    path.write_bytes(FIXTURE.read_bytes() + b" ")
    with pytest.raises(ValueError, match="hash"):
        replay_route_fixture(path)


def test_api_auth_ui_and_replay():
    app = create_app(lifespan_enabled=False)
    app.state.historical_read_token = "test-only"
    with TestClient(app) as client:
        assert client.get("/api/v1/route-evidence").status_code == 401
        response = client.get("/api/v1/route-evidence", headers={"Authorization": "Bearer test-only"})
        assert response.status_code == 200
        assert response.json()["report"]["evidence_id"] == EVIDENCE_ID
        assert client.get("/dashboard/route-evidence").status_code == 200


def test_route_exclusion_overrides_legacy_buy_score():
    rows = ({"wallet": WALLET, "mint": "mint", "buy_count": 100, "venues": ["dex"]},)
    assert rank_wallet_token_candidates(rows)[0]["score_bps"] > 0
    assert rank_wallet_token_candidates(rows, excluded_subjects=frozenset({(WALLET, "mint")}))[0]["score_bps"] == 0
