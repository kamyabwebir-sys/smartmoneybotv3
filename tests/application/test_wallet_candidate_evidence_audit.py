from smart_money.application.wallet_candidate_evidence import build_wallet_candidate_evidence
from smart_money.application.wallet_candidate_evidence_audit import (
    build_wallet_candidate_evidence_audit_receipt,
)
from smart_money.application.wallet_candidate_evidence_replay import (
    replay_verify_wallet_candidate_evidence,
)
from smart_money.application.wallet_candidate_evidence_store_verifier import (
    WalletCandidateEvidenceStoreVerificationReceipt,
)
from smart_money.application.wallet_candidate_feature import WalletCandidateFeature
from smart_money.core.ids import deterministic_id


def test_wallet_candidate_evidence_audit_binds_replay_and_store() -> None:
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
    replay = replay_verify_wallet_candidate_evidence(feature, evidence)
    verification_identity = {
        "evidence_id": evidence.evidence_id,
        "matches": True,
        "schema_version": "wallet_candidate_evidence_store_verifier.v1",
    }
    verification = WalletCandidateEvidenceStoreVerificationReceipt(
        **verification_identity,
        verification_id=deterministic_id(
            "wallet_candidate_evidence_store_verification", verification_identity
        ),
    )
    audit = build_wallet_candidate_evidence_audit_receipt(
        evidence=evidence,
        replay_receipt=replay,
        store_verification=verification,
    )
    assert audit.replay_matches is True
    assert audit.audit_id
