from smart_money.application.wallet_candidate_evidence import (
    WalletCandidateEvidenceStatus,
    build_wallet_candidate_evidence,
)
from smart_money.application.wallet_candidate_feature import WalletCandidateFeature
from smart_money.core.ids import deterministic_id


def test_wallet_candidate_evidence_is_proposed_from_explicit_features() -> None:
    identity = {
        "activity_count": 3,
        "buy_ratio_bps": 6000,
        "cohort_count": 1,
        "data_completeness_bps": 9000,
        "early_entry_consistency_bps": 5000,
        "profile_id": "profile-a",
        "relationship_count": 2,
        "schema_version": "wallet_candidate_feature.v1",
        "wallet": "wallet-a",
    }
    feature = WalletCandidateFeature(
        **identity,
        feature_id=deterministic_id("wallet_candidate_feature", identity),
    )
    evidence = build_wallet_candidate_evidence(
        feature,
        provenance={"cluster": "cluster-1", "source": "wallet-intelligence"},
    )
    assert evidence.status is WalletCandidateEvidenceStatus.PROPOSED
    assert "HAS_WALLET_RELATIONSHIPS" in evidence.reason_codes
    assert evidence.evidence_id
