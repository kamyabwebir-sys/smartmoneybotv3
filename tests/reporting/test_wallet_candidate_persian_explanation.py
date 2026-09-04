from smart_money.application.wallet_candidate_evidence import build_wallet_candidate_evidence
from smart_money.application.wallet_candidate_feature import WalletCandidateFeature
from smart_money.application.wallet_candidate_read_model import WalletCandidateReadRow
from smart_money.application.wallet_ranking import rank_wallet_candidates
from smart_money.reporting.wallet_candidate_persian_explanation import explain_wallet_candidate
from smart_money.core.ids import deterministic_id


def test_explain_wallet_candidate_in_persian() -> None:
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
    row = WalletCandidateReadRow(evidence, ranking.rows[0])
    explanation = explain_wallet_candidate(row)
    assert "ولت" in explanation.summary
    assert "توصیهٔ خرید یا فروش نیست" in explanation.provenance
    assert explanation.explanation_id
