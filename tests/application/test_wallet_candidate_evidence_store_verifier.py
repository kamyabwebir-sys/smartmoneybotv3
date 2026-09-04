from smart_money.adapters.persistence.wallet_candidate_evidence_store import (
    JsonWalletCandidateEvidenceStore,
)
from smart_money.application.wallet_candidate_evidence import build_wallet_candidate_evidence
from smart_money.application.wallet_candidate_evidence_store_verifier import (
    verify_wallet_candidate_evidence_store,
)
from smart_money.application.wallet_candidate_feature import WalletCandidateFeature
from smart_money.core.ids import deterministic_id


def test_wallet_candidate_evidence_store_verification(tmp_path) -> None:
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
    store = JsonWalletCandidateEvidenceStore(tmp_path / "evidence.json")
    store.append(evidence)
    verification = verify_wallet_candidate_evidence_store(store, evidence)
    assert verification.matches is True
    assert verification.evidence_id == evidence.evidence_id
