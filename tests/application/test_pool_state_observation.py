import json
from copy import deepcopy
from pathlib import Path

import pytest

from smart_money.application.pool_state_observation import observe_pool_state
from smart_money.application.verified_swap_legs import verify_swap_legs
from smart_money.application.wallet_route_evidence import project_wallet_route
from smart_money.adapters.persistence.wallet_route_fixture import WALLET

ROOT = Path(__file__).resolve().parents[2] / "fixtures/solana/mainnet"


def inputs():
    raw = json.loads((ROOT / "s12-cycle.json").read_bytes())["result"]
    snapshot = json.loads((ROOT / "s12-pool-observation.json").read_bytes())
    return raw, snapshot, verify_swap_legs(raw, project_wallet_route(raw, WALLET))["legs"]


def test_real_pool_snapshots_are_not_historical():
    raw, snapshot, legs = inputs()
    for leg in legs:
        result = observe_pool_state(snapshot, leg, raw["slot"])
        assert result["identity_matches"]
        assert result["observed_slot"] == 447647895
        assert result["temporal_relation"] == "AFTER"
        assert not result["historical_state_verified"]


@pytest.mark.parametrize("case", ["owner", "missing", "length", "executable", "mint", "vault", "slot", "duplicate"])
def test_pool_corruption_rejected(case):
    raw, snapshot, legs = inputs()
    leg = deepcopy(legs[0])
    account = snapshot["response"]["result"]["value"][0]
    if case == "owner":
        account["owner"] = "wrong"
    elif case == "missing":
        snapshot["response"]["result"]["value"][0] = None
    elif case == "length":
        account["data"][0] = "AA=="
    elif case == "executable":
        account["executable"] = True
    elif case == "mint":
        leg["input_mint"] = "wrong"
    elif case == "vault":
        leg["input_vault"] = "wrong"
    elif case == "slot":
        snapshot["response"]["result"]["context"]["slot"] = True
    else:
        snapshot["addresses"][1] = snapshot["addresses"][0]
    with pytest.raises(ValueError):
        observe_pool_state(snapshot, leg, raw["slot"])
