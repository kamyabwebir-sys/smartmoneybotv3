from smart_money.application.wallet_candidate_evidence import build_wallet_candidate_evidence
from smart_money.application.wallet_candidate_evidence_query import (
    query_wallet_candidate_evidence,
)
from smart_money.application.wallet_candidate_evidence_read_model import (
    build_wallet_candidate_evidence_read_model,
)
from smart_money.application.wallet_candidate_feature import WalletCandidateFeature
from smart_money.application.wallet_ranking import rank_wallet_candidates
from smart_money.core.ids import deterministic_id


def test_wallet_candidate_evidence_query_filters_read_model() -> None:
    identity = {
        "activity_count": 3,
        "buy_ratio_bps": 6000,
        "cohort_count": 1,
        "data_completeness_bps": 9000,
        "early_entry_consistency_bps": 7000,
        "profile_id": "profile-a",
        "relationship_count": 2,
        "schema_version": "wallet_candidate_feature.v1",
        "wallet": "wallet-a",
    }
    feature = WalletCandidateFeature(
        **identity,
        feature_id=deterministic_id("wallet_candidate_feature", identity),
    )
    evidence = build_wallet_candidate_evidence(feature, provenance={"source": "test"})
    ranking = rank_wallet_candidates((evidence,))
    model = build_wallet_candidate_evidence_read_model(
        (evidence,), ranking_rows=ranking.rows
    )
    result = query_wallet_candidate_evidence(
        model, wallet=" wallet-a ", min_score_bps=1, max_rank=1
    )
    assert len(result.rows) == 1
    assert result.rows[0].evidence.evidence_id == evidence.evidence_id
