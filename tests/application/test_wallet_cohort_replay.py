from smart_money.application.wallet_behavior_fingerprint import WalletBehaviorFingerprint
from smart_money.application.wallet_cohort_detection import detect_wallet_cohorts
from smart_money.application.wallet_cohort_replay import replay_verify_wallet_cohort
from smart_money.core.ids import deterministic_id


def _fingerprint(wallet: str) -> WalletBehaviorFingerprint:
    identity = {
        "activity_per_observation": 3, "buy_ratio_bps": 7000,
        "data_completeness_bps": 10000, "profile_id": f"profile-{wallet}",
        "schema_version": "wallet_behavior_fingerprint.v1", "sell_ratio_bps": 3000,
        "token_observation_ratio_bps": 4000, "unknown_ratio_bps": 0, "wallet": wallet,
    }
    return WalletBehaviorFingerprint(
        **identity, fingerprint_id=deterministic_id("wallet_behavior_fingerprint", identity)
    )


def test_wallet_cohort_replays_from_fingerprints() -> None:
    fingerprints = (_fingerprint("W1"), _fingerprint("W2"))
    cohort = detect_wallet_cohorts(fingerprints)[0]
    receipt = replay_verify_wallet_cohort(cohort, tuple(reversed(fingerprints)))
    assert receipt.matches is True
    assert receipt.cohort_id == cohort.cohort_id
