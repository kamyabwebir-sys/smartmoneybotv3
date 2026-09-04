from smart_money.application.wallet_candidate_evidence import build_wallet_candidate_evidence
from smart_money.application.wallet_candidate_evidence_audit import (
    WalletCandidateEvidenceAuditReceipt,
)
from smart_money.application.wallet_candidate_evidence_read_model import (
    build_wallet_candidate_evidence_read_model,
)
from smart_money.application.wallet_candidate_feature import WalletCandidateFeature
from smart_money.application.wallet_ranking import rank_wallet_candidates
from smart_money.core.ids import deterministic_id


def test_wallet_candidate_evidence_read_model_integrates_ranking_and_audit() -> None:
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
    audit_identity = {
        "evidence_id": evidence.evidence_id,
        "replay_id": "replay-1",
        "replay_matches": True,
        "schema_version": "wallet_candidate_evidence_audit.v1",
        "store_verification_id": "verification-1",
    }
    audit = WalletCandidateEvidenceAuditReceipt(
        **audit_identity,
        audit_id=deterministic_id("wallet_candidate_evidence_audit", audit_identity),
    )
    model = build_wallet_candidate_evidence_read_model(
        (evidence,), ranking_rows=ranking.rows, audits=(audit,)
    )
    assert model.rows[0].ranking is not None
    assert model.rows[0].audit == audit
