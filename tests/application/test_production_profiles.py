from smart_money.application.production_profiles import (
    build_wallet_production_profile,
)
from smart_money.application.wallet_intelligence_profile import WalletIntelligenceProfile
from smart_money.core.ids import deterministic_id


def test_wallet_production_profile_is_deterministic() -> None:
    identity = {
        "activity_count": 3,
        "buy_count": 2,
        "data_completeness_bps": 9000,
        "distinct_token_observation_total": 3,
        "native_delta_total": 1,
        "observed_from_slot": 10,
        "observed_to_slot": 20,
        "observation_count": 1,
        "observation_ids": ("observation-1",),
        "schema_version": "wallet_intelligence_profile.v1",
        "sell_count": 1,
        "token_delta_total": 4,
        "unknown_count": 0,
        "wallet": "wallet-1",
    }
    profile = WalletIntelligenceProfile(
        profile_id=deterministic_id("wallet_intelligence_profile", identity),
        **identity,
    )
    production = build_wallet_production_profile(profile)
    assert production.wallet == "wallet-1"
    assert production.activity_count == 3
    assert production == build_wallet_production_profile(profile)
