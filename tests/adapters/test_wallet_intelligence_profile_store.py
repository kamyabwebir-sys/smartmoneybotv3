from smart_money.adapters.persistence.wallet_intelligence_profile_store import JsonWalletIntelligenceProfileStore
from smart_money.application.wallet_intelligence_profile import WalletIntelligenceProfile
from smart_money.core.ids import deterministic_id


def _profile() -> WalletIntelligenceProfile:
    identity = {
        "activity_count": 2, "buy_count": 1, "data_completeness_bps": 10000,
        "distinct_token_observation_total": 1, "native_delta_total": -1,
        "observed_from_slot": 10, "observed_to_slot": 20, "observation_count": 1,
        "observation_ids": ("obs-1",), "schema_version": "wallet_intelligence_profile.v1",
        "sell_count": 1, "token_delta_total": 3, "unknown_count": 0, "wallet": "W",
    }
    return WalletIntelligenceProfile(
        **identity,
        profile_id=deterministic_id("wallet_intelligence_profile", identity),
    )


def test_profile_store_is_idempotent_and_reloadable(tmp_path) -> None:
    path = tmp_path / "profile.json"
    profile = _profile()
    store = JsonWalletIntelligenceProfileStore(path)
    assert store.save(profile) == profile.profile_id
    assert store.save(profile) == profile.profile_id
    restored = JsonWalletIntelligenceProfileStore(path)
    assert restored.load() == profile
