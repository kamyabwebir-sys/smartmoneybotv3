from smart_money.application.wallet_candidate_evidence import (
    build_wallet_candidate_evidence,
)
from smart_money.application.wallet_candidate_feature import WalletCandidateFeature
from smart_money.application.wallet_ranking import rank_wallet_candidates
from smart_money.core.ids import deterministic_id


def _evidence(wallet: str, early: int):
    identity = {
        "activity_count": 5,
        "buy_ratio_bps": 5000,
        "cohort_count": 1,
        "data_completeness_bps": 9000,
        "early_entry_consistency_bps": early,
        "profile_id": f"profile-{wallet}",
        "relationship_count": 2,
        "schema_version": "wallet_candidate_feature.v1",
        "wallet": wallet,
    }
    feature = WalletCandidateFeature(
        **identity,
        feature_id=deterministic_id("wallet_candidate_feature", identity),
    )
    return build_wallet_candidate_evidence(feature, provenance={"source": "test"})


def test_wallet_ranking_is_deterministic() -> None:
    ranking = rank_wallet_candidates((_evidence("wallet-b", 2000), _evidence("wallet-a", 8000)))
    assert ranking.rows[0].wallet == "wallet-a"
    assert ranking.rows[0].rank == 1
    assert ranking.rows[0].score_bps > ranking.rows[1].score_bps
