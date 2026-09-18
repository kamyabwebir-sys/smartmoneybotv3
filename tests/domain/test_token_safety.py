import pytest

from smart_money.core.ids import deterministic_id
from smart_money.domain.token_safety import TokenSafetyObservation


def test_token_safety_observation_is_deterministic_and_immutable():
    identity = {
        "deployer": "DEPLOYER", "freeze_authority": None,
        "holder_concentration_bps": 1200, "liquidity_amount": 500000,
        "mint": None, "observed_at": 10,
        "schema_version": "token_safety_observation.v1", "token": "TOKEN",
        "update_authority": "UPDATER",
    }
    observation = TokenSafetyObservation(
        token="TOKEN", observed_at=10, mint_authority=None,
        freeze_authority=None, update_authority="UPDATER",
        liquidity_amount=500000, holder_concentration_bps=1200,
        deployer="DEPLOYER",
        observation_id=deterministic_id("token_safety_observation", identity),
    )
    assert observation.canonical_dict()["token"] == "TOKEN"
    with pytest.raises((AttributeError, TypeError)):
        observation.token = "OTHER"


def test_holder_concentration_is_bounded():
    with pytest.raises(ValueError, match="10000"):
        TokenSafetyObservation(
            token="TOKEN", observed_at=1, mint_authority=None,
            freeze_authority=None, update_authority=None,
            liquidity_amount=1, holder_concentration_bps=10001,
            deployer="DEPLOYER", observation_id="bad"
        )
