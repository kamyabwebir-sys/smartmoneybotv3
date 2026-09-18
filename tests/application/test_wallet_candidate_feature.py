from smart_money.application.wallet_candidate_feature import WalletCandidateFeature
from smart_money.core.ids import deterministic_id


def test_wallet_candidate_feature_is_deterministic_and_validated() -> None:
    identity = {
        "activity_count": 10,
        "buy_ratio_bps": 6500,
        "cohort_count": 2,
        "data_completeness_bps": 9000,
        "early_entry_consistency_bps": 7000,
        "profile_id": "profile-1",
        "relationship_count": 3,
        "schema_version": "wallet_candidate_feature.v1",
        "wallet": "wallet-a",
    }
    feature = WalletCandidateFeature(
        **identity,
        feature_id=deterministic_id("wallet_candidate_feature", identity),
    )
    assert feature.canonical_dict()["wallet"] == "wallet-a"
    assert feature.feature_id
