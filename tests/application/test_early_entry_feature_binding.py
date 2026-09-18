from smart_money.application.early_entry_consistency import EarlyEntryConsistency
from smart_money.application.early_entry_feature_binding import bind_early_entry_features
from smart_money.application.wallet_candidate_feature import WalletCandidateFeature
from smart_money.core.ids import deterministic_id


def test_bind_early_entry_features() -> None:
    feature_identity = {
        "activity_count": 2,
        "buy_ratio_bps": 5000,
        "cohort_count": 1,
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
    consistency_identity = {
        "activity_ids": ("activity-1",),
        "consistency_bps": 10000,
        "early_entry_count": 1,
        "evaluated_buy_count": 1,
        "schema_version": "early_entry_consistency.v1",
        "token_ids": ("token-1",),
        "wallet": "wallet-a",
    }
    consistency = EarlyEntryConsistency(
        **consistency_identity,
        consistency_id=deterministic_id("early_entry_consistency", consistency_identity),
    )
    bound = bind_early_entry_features((feature,), (consistency,))
    assert bound[0].early_entry_consistency_bps == 10000
