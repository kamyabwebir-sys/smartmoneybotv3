import json
from copy import deepcopy
from pathlib import Path
import importlib.util
import sys

import pytest

from smart_money.adapters.persistence.wallet_route_fixture import WALLET, SIGNATURE
from smart_money.application.live_route_batch import run_route_checked_batch
from smart_money.application.wallet_route_evidence import project_wallet_route
from smart_money.application.verified_swap_legs import verify_swap_legs

ROOT = Path(__file__).resolve().parents[2]


def fixture():
    return json.loads((ROOT / "fixtures/solana/mainnet/s12-cycle.json").read_bytes())


def test_two_real_legs_and_exact_pool_mapping():
    raw = fixture()["result"]
    result = verify_swap_legs(raw, project_wallet_route(raw, WALLET))
    assert not result["unresolved"]
    assert [r["pool"] for r in result["legs"]] == [
        "4MXybVn82rBxjvANiMpmvYUQejRzwkiTnjDT8NQmHMRe",
        "3RZcRvdU4osDJKDmhCyKqhU5eF8F8Lsy9BDghAM8RmvA"]
    first, second = result["legs"]
    assert first["amount_in_raw"] == "80000000000"
    assert first["amount_out_raw"] == second["amount_in_raw"] == "185305375"
    assert second["amount_out_raw"] == "235068942933"
    assert not result["full_route_verified"]


@pytest.mark.parametrize("mutation", ["data", "vault", "height", "amount", "program"])
def test_no_false_verified_leg(mutation):
    raw = fixture()["result"]
    group = raw["meta"]["innerInstructions"][0]["instructions"]
    if mutation == "data":
        group[3]["data"] = "1"
    elif mutation == "vault":
        group[3]["accounts"][6] = "wrong"
    elif mutation == "height":
        group[4]["stackHeight"] = None
    elif mutation == "amount":
        group[4]["parsed"]["info"]["tokenAmount"]["amount"] = "7"
    else:
        group[3]["programId"] = "unknown"
    result = verify_swap_legs(raw, project_wallet_route(raw, WALLET))
    assert not any(x["instruction"] == "swap_base_input" for x in result["legs"])


def test_single_fetch_dedup_exclusion_and_deterministic_replay():
    calls = []
    def page(*args):
        return {"result": [{"signature": SIGNATURE}, {"signature": SIGNATURE}]}
    def fetch(signature):
        calls.append(signature)
        return fixture()
    first = run_route_checked_batch(page, fetch, WALLET)
    assert calls == [SIGNATURE]
    assert first["candidate_count"] == 0
    assert len(first["ranking"]) == 2
    assert all(x["score_bps"] == 0 for x in first["ranking"])
    assert not first["gate"]["passed"]
    assert run_route_checked_batch(page, fetch, WALLET) == first


@pytest.mark.parametrize("mode", ["null", "failed", "wrong_signature", "timeout"])
def test_bad_rpc_never_becomes_candidate(mode):
    def fetch(_):
        result = deepcopy(fixture())
        if mode == "timeout":
            raise TimeoutError()
        if mode == "null":
            result["result"] = None
        elif mode == "failed":
            result["result"]["meta"]["err"] = "failed"
        else:
            result["result"]["transaction"]["signatures"][0] = "wrong"
        return result
    result = run_route_checked_batch(lambda *a: {"result": [{"signature": SIGNATURE}]}, fetch, WALLET)
    assert result["failures"] and not result["ranking"]
    assert result["candidate_count"] == 0


def test_runner_end_to_end_with_real_fixture(tmp_path, monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location("tested_live_rpc_runner", ROOT / "scripts/live_rpc_runner.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    calls = []
    class Fetcher:
        def __init__(self, config):
            pass
        def capture_signatures(self, *args):
            calls.append("page")
            return {"result": [{"signature": SIGNATURE}]}
        def capture_transaction(self, signature):
            calls.append(signature)
            return fixture()
    monkeypatch.setattr(module, "SolanaRPCFetcher", Fetcher)
    monkeypatch.setenv("SOLANA_RPC_URL", "https://example.invalid")
    path = tmp_path / "session.json"
    monkeypatch.setattr(sys, "argv", ["runner", "--wallet", WALLET, "--output", str(path)])
    assert module.main() == 0
    saved = json.loads(path.read_text())
    assert json.loads(capsys.readouterr().out) == saved
    assert calls == ["page", SIGNATURE]
    assert saved["candidate_count"] == 0
    assert len(saved["swap_legs"][0]["legs"]) == 2
    assert "audit" not in saved and "replay" not in saved
