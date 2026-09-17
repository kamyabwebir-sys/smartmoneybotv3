import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from smart_money.adapters.persistence.wallet_route_fixture import (
    PURCHASE_ID,
    PURCHASE_WALLET,
    replay_purchase_fixture,
)
from smart_money.application.directional_purchase import (
    evaluate_directional_purchase,
    rank_purchase_evaluations,
)
from smart_money.application.live_route_batch import run_route_checked_batch
from smart_money.application.verified_swap_legs import ALPHABET, _decode

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures/solana/mainnet/s12-trending-buy-candidate.json"
MINT = "mMHUFPJma7sGuFxYteoHJkfzb5iW6oLxsvVnUYfSTNK"


def payload():
    return json.loads(FIXTURE.read_bytes())


def encode(data):
    number, result = int.from_bytes(data, "big"), ""
    while number:
        number, index = divmod(number, 58)
        result = ALPHABET[index] + result
    return "1" * (len(data) - len(data.lstrip(b"\0"))) + result


def test_real_purchase_is_accepted_with_exact_amounts():
    raw = payload()["result"]
    before = deepcopy(raw)
    result = evaluate_directional_purchase(raw, PURCHASE_WALLET)
    assert raw == before
    purchase = result["purchase"]
    assert purchase["accepted"] and purchase["evidence_id"] == PURCHASE_ID
    assert purchase["quote_spent_raw"] == "9486854"
    assert purchase["amount_received_raw"] == "305853508248"
    assert purchase["auxiliary_quote_outflow_raw"] == "47434"
    assert purchase["mint"] == MINT
    assert purchase["human_review_required"]
    assert not purchase["historical_pool_state_verified"]
    assert not purchase["full_jupiter_instruction_decoded"]
    assert [leg["instruction"] for leg in result["swaps"]["legs"]] == ["swap_v2_exact_input", "swap_base_input"]
    assert result["swaps"]["legs"][0]["pool"] == "D6bRhQUcR9B7bPbbqgxpE17MjyUjBtr8hHQCcJoHrrv1"
    assert result["swaps"]["legs"][1]["pool"] == "5mM3i5gZ8KGjJc4MRMsvdUWRWaiW5i1rfUSfvkpXQXg8"
    rows = rank_purchase_evaluations([result])
    assert rows[0]["mint"] == MINT and rows[0]["ranking_eligible"] and rows[0]["score_bps"] > 0
    assert all(not row["ranking_eligible"] and row["score_bps"] == 0 for row in rows[1:])
    assert evaluate_directional_purchase(raw, PURCHASE_WALLET) == result


@pytest.mark.parametrize("mutation", ["clmm_data", "exact_output", "vault", "token_fee", "account_program", "instruction_program",
                                     "hook", "owner", "missing_balance", "mint", "native", "signer", "amount", "failed",
                                     "unparsed_token", "wrong_height", "extra_program", "source_account"])
def test_mutations_cannot_enter_positive_ranking(mutation):
    data = payload()
    raw, meta = data["result"], data["result"]["meta"]
    ins = meta["innerInstructions"][0]["instructions"]
    if mutation == "clmm_data":
        ins[0]["data"] = "1"
    elif mutation == "exact_output":
        changed = bytearray(_decode(ins[0]["data"]))
        changed[40] = 0
        ins[0]["data"] = encode(changed)
    elif mutation == "vault":
        ins[0]["accounts"][5] = "wrong"
    elif mutation == "token_fee":
        row = next(r for r in meta["postTokenBalances"] if r["accountIndex"] == 17)
        row["uiTokenAmount"]["amount"] = str(int(row["uiTokenAmount"]["amount"]) - 1)
    elif mutation == "account_program":
        meta["postTokenBalances"][0]["programId"] = "wrong"
    elif mutation == "instruction_program":
        ins[5]["programId"] = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
    elif mutation == "hook":
        ins.insert(6, {"programId": "unknown-hook", "stackHeight": 4, "accounts": [], "data": "1"})
    elif mutation == "owner":
        meta["postTokenBalances"][0]["owner"] = "other"
    elif mutation == "missing_balance":
        meta["postTokenBalances"].pop(0)
    elif mutation == "mint":
        ins[0]["accounts"][11] = "wrong"
    elif mutation == "native":
        meta["postBalances"][0] -= 1
    elif mutation == "signer":
        raw["transaction"]["message"]["accountKeys"][0]["signer"] = False
    elif mutation == "amount":
        ins[4]["parsed"]["info"]["tokenAmount"]["amount"] = "1"
    elif mutation == "failed":
        meta["err"] = {"InstructionError": [2, "error"]}
    elif mutation == "unparsed_token":
        ins[4].pop("parsed")
    elif mutation == "wrong_height":
        ins[4]["stackHeight"] = 4
    elif mutation == "extra_program":
        raw["transaction"]["message"]["instructions"].append({"programId": "unknown", "data": "1", "accounts": []})
    else:
        ins[3]["accounts"][4] = "wrong"
    signature = raw["transaction"]["signatures"][0]
    session = run_route_checked_batch(lambda *a: {"result": [{"signature": signature}]}, lambda _: data, PURCHASE_WALLET)
    assert session["candidate_count"] == 0
    assert all(not row["ranking_eligible"] for row in session["ranking"])
    assert not session["gate"]["passed"]


def test_replay_id_binds_instruction_data():
    raw = payload()["result"]
    ins = raw["meta"]["innerInstructions"][0]["instructions"][0]
    changed = bytearray(_decode(ins["data"]))
    changed[16] = 1  # valid minimum out changes; actual received amount still clears it
    ins["data"] = encode(changed)
    result = evaluate_directional_purchase(raw, PURCHASE_WALLET)["purchase"]
    assert result["accepted"] and result["evidence_id"] != PURCHASE_ID


def test_positive_runner_to_persisted_ranking(tmp_path, monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location("positive_live_runner", ROOT / "scripts/live_rpc_runner.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    data = payload()
    signature = data["result"]["transaction"]["signatures"][0]
    calls = []
    class Fetcher:
        def __init__(self, config):
            pass
        def capture_signatures(self, *args):
            return {"result": [{"signature": signature}, {"signature": signature}]}
        def capture_transaction(self, sig):
            calls.append(sig)
            return data
    monkeypatch.setattr(module, "SolanaRPCFetcher", Fetcher)
    monkeypatch.setenv("SOLANA_RPC_URL", "https://example.invalid")
    output = tmp_path / "positive.json"
    monkeypatch.setattr(sys, "argv", ["runner", "--wallet", PURCHASE_WALLET, "--output", str(output)])
    assert module.main() == 0
    saved = json.loads(output.read_text())
    assert saved == json.loads(capsys.readouterr().out)
    assert calls == [signature] and saved["candidate_count"] == 1
    assert saved["ranking"][0]["mint"] == MINT
    assert not saved["gate"]["passed"]


def test_purchase_api_and_fixture_integrity(tmp_path):
    replay = replay_purchase_fixture(FIXTURE)
    assert replay["eligible_count"] == 1
    corrupt = tmp_path / "bad.json"
    corrupt.write_bytes(FIXTURE.read_bytes() + b" ")
    with pytest.raises(ValueError, match="hash"):
        replay_purchase_fixture(corrupt)
    app = create_app(lifespan_enabled=False)
    app.state.historical_read_token = "test"
    with TestClient(app) as client:
        assert client.get("/api/v1/route-evidence?sample=purchase").status_code == 401
        good = client.get("/api/v1/route-evidence?sample=purchase", headers={"Authorization": "Bearer test"})
        assert good.status_code == 200 and good.json()["eligible_count"] == 1
        assert client.get("/api/v1/route-evidence?sample=../../bad", headers={"Authorization": "Bearer test"}).status_code == 422
