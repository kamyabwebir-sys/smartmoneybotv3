from smart_money.application.behavior_fingerprint_feature_binding import (
    bind_behavior_fingerprint_features,
)
from smart_money.application.wallet_behavior_fingerprint import WalletBehaviorFingerprint
from smart_money.application.wallet_candidate_feature import WalletCandidateFeature
from smart_money.core.ids import deterministic_id


def test_bind_behavior_fingerprint_features() -> None:
    feature_identity = {
        "activity_count": 3,
        "buy_ratio_bps": 0,
        "cohort_count": 1,
        "data_completeness_bps": 0,
        "early_entry_consistency_bps": 5000,
        "profile_id": "profile-a",
        "relationship_count": 2,
        "schema_version": "wallet_candidate_feature.v1",
        "wallet": "wallet-a",
    }
    feature = WalletCandidateFeature(
        **feature_identity,
        feature_id=deterministic_id("wallet_candidate_feature", feature_identity),
    )
    fingerprint_identity = {
        "activity_per_observation": 3,
        "buy_ratio_bps": 6000,
        "data_completeness_bps": 9000,
        "profile_id": "profile-a",
        "schema_version": "wallet_behavior_fingerprint.v1",
        "sell_ratio_bps": 3000,
        "token_observation_ratio_bps": 5000,
        "unknown_ratio_bps": 1000,
        "wallet": "wallet-a",
    }
    fingerprint = WalletBehaviorFingerprint(
        **fingerprint_identity,
        fingerprint_id=deterministic_id(
            "wallet_behavior_fingerprint", fingerprint_identity
        ),
    )
    bound = bind_behavior_fingerprint_features((feature,), (fingerprint,))
    assert bound[0].buy_ratio_bps == 6000
    assert bound[0].data_completeness_bps == 9000
    assert bound[0].activity_count == 3
