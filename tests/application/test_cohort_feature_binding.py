from smart_money.application.cohort_feature_binding import bind_cohort_features
from smart_money.application.wallet_candidate_feature import WalletCandidateFeature
from smart_money.application.wallet_cohort_detection import WalletCohort
from smart_money.core.ids import deterministic_id


def test_bind_cohort_features_counts_membership() -> None:
    feature_identity = {
        "activity_count": 1,
        "buy_ratio_bps": 1000,
        "cohort_count": 0,
        "data_completeness_bps": 9000,
        "early_entry_consistency_bps": 0,
        "profile_id": "profile-a",
        "relationship_count": 1,
        "schema_version": "wallet_candidate_feature.v1",
        "wallet": "wallet-a",
    }
    feature = WalletCandidateFeature(
        **feature_identity,
        feature_id=deterministic_id("wallet_candidate_feature", feature_identity),
    )
    cohort_identity = {
        "cohort_key": (1, 1, 1, 1),
        "fingerprint_ids": ("fp-a",),
        "schema_version": "wallet_cohort_detection.v1",
        "wallets": ("wallet-a",),
    }
    cohort = WalletCohort(
        **cohort_identity,
        cohort_id=deterministic_id("wallet_cohort", cohort_identity),
    )
    bound = bind_cohort_features((feature,), (cohort,))
    assert bound[0].cohort_count == 1
    assert bound[0].wallet == "wallet-a"
