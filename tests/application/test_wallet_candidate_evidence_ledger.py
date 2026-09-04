from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.wallet_candidate_evidence import build_wallet_candidate_evidence
from smart_money.application.wallet_candidate_evidence_ledger import (
    ingest_wallet_candidate_evidence,
)
from smart_money.application.wallet_candidate_feature import WalletCandidateFeature
from smart_money.core.ids import deterministic_id


def test_wallet_candidate_evidence_ledger_projection() -> None:
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
    ledger = EvidenceGroundingLedger()
    evidence_id = ingest_wallet_candidate_evidence(evidence, ledger)
    assert ledger.get(evidence_id) is not None
    assert ledger.entry_count == 1
