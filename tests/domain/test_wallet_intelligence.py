import pytest

from smart_money.core.ids import deterministic_id
from smart_money.domain.wallet_intelligence import WalletIntelligenceObservation


def test_wallet_intelligence_observation_is_deterministic():
    identity = {
        "activity_count": 3, "buy_count": 2, "data_completeness_bps": 9000,
        "distinct_token_count": 2, "native_delta_total": -10,
        "observed_from_slot": 1, "observed_to_slot": 9,
        "schema_version": "wallet_intelligence_observation.v1", "sell_count": 1,
        "token_delta_total": 30, "unknown_count": 0, "wallet": "W",
    }
    observation = WalletIntelligenceObservation(
        wallet="W", observed_from_slot=1, observed_to_slot=9,
        activity_count=3, buy_count=2, sell_count=1, unknown_count=0,
        distinct_token_count=2, token_delta_total=30, native_delta_total=-10,
        data_completeness_bps=9000,
        observation_id=deterministic_id("wallet_intelligence_observation", identity),
    )
    assert observation == WalletIntelligenceObservation(**{
        **{key: value for key, value in identity.items() if key != "schema_version"},
        "observation_id": observation.observation_id,
    })
    with pytest.raises((AttributeError, TypeError)):
        observation.wallet = "OTHER"


def test_wallet_intelligence_rejects_inconsistent_counts():
    with pytest.raises(ValueError, match="reconcile"):
        WalletIntelligenceObservation(
            wallet="W", observed_from_slot=1, observed_to_slot=1,
            activity_count=1, buy_count=1, sell_count=1, unknown_count=0,
            distinct_token_count=1, token_delta_total=0, native_delta_total=0,
            data_completeness_bps=10000, observation_id="bad",
        )
