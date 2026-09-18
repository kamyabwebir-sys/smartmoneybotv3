from smart_money.application.wallet_behavior_fingerprint import (
    WalletBehaviorFingerprint,
)
from smart_money.application.wallet_cohort_detection import detect_wallet_cohorts
from smart_money.core.ids import deterministic_id


def _fingerprint(wallet: str, fingerprint_id: str) -> WalletBehaviorFingerprint:
    identity = {
        "activity_per_observation": 3,
        "buy_ratio_bps": 7000,
        "data_completeness_bps": 10000,
        "profile_id": f"profile-{wallet}",
        "schema_version": "wallet_behavior_fingerprint.v1",
        "sell_ratio_bps": 3000,
        "token_observation_ratio_bps": 4000,
        "unknown_ratio_bps": 0,
        "wallet": wallet,
    }
    return WalletBehaviorFingerprint(
        **identity,
        fingerprint_id=deterministic_id("wallet_behavior_fingerprint", identity),
    )


def test_wallets_with_same_behavior_buckets_form_deterministic_cohort() -> None:
    first = _fingerprint("W1", "ignored-1")
    second = _fingerprint("W2", "ignored-2")
    cohorts = detect_wallet_cohorts((second, first), bucket_size_bps=1000)
    assert len(cohorts) == 1
    assert cohorts[0].wallets == ("W1", "W2")
    assert cohorts[0].fingerprint_ids == (first.fingerprint_id, second.fingerprint_id)
    assert cohorts == detect_wallet_cohorts((first, second), bucket_size_bps=1000)
