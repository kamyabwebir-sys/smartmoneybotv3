import pytest

from smart_money.application.token_safety_parser import parse_token_safety_observation


def _raw():
    return {
        "token": "TOKEN",
        "observed_at": 10,
        "mint_authority": None,
        "freeze_authority": None,
        "update_authority": "UPDATER",
        "liquidity_amount": 1000,
        "holder_concentration_bps": 1200,
        "deployer": "DEPLOYER",
    }


def test_parser_builds_deterministic_observation():
    observation = parse_token_safety_observation(_raw())
    assert observation.token == "TOKEN"
    assert observation.observation_id
    assert observation == parse_token_safety_observation(dict(_raw()))


def test_parser_rejects_unknown_keys():
    raw = _raw()
    raw["verdict"] = "SAFE"
    with pytest.raises(ValueError, match="keys"):
        parse_token_safety_observation(raw)
