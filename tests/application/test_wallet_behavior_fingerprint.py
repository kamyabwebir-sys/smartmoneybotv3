from smart_money.application.wallet_behavior_fingerprint import project_wallet_behavior_fingerprint
from smart_money.application.wallet_intelligence_profile import WalletIntelligenceProfile
from smart_money.core.ids import deterministic_id


def test_wallet_behavior_fingerprint_is_deterministic() -> None:
    identity = {
        "activity_count": 3, "buy_count": 2, "data_completeness_bps": 10000,
        "distinct_token_observation_total": 2, "native_delta_total": -10,
        "observed_from_slot": 1, "observed_to_slot": 9, "observation_count": 1,
        "observation_ids": ("obs-1",), "schema_version": "wallet_intelligence_profile.v1",
        "sell_count": 1, "token_delta_total": 30, "unknown_count": 0, "wallet": "W",
    }
    profile = WalletIntelligenceProfile(
        **identity, profile_id=deterministic_id("wallet_intelligence_profile", identity)
    )
    fingerprint = project_wallet_behavior_fingerprint(profile)
    assert fingerprint.buy_ratio_bps == 6666
    assert fingerprint.sell_ratio_bps == 3333
    assert fingerprint.unknown_ratio_bps == 1
    assert fingerprint.fingerprint_id == project_wallet_behavior_fingerprint(profile).fingerprint_id
