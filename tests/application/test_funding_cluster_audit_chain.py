from smart_money.application.funding_cluster_audit_chain import (
    build_funding_cluster_audit_chain_receipt,
)
from smart_money.application.funding_cluster_store_audit import (
    FundingClusterStoreAuditReceipt,
)
from smart_money.application.funding_cluster_store_audit_store_verifier import (
    FundingClusterStoreAuditStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id


def test_funding_cluster_audit_chain_binds_audit_and_verification() -> None:
    audit_identity = {
        "cluster_id": "cluster-1",
        "ledger_receipt_id": "ledger-1",
        "replay_id": "replay-1",
        "replay_matches": True,
        "schema_version": "funding_cluster_store_audit.v1",
        "store_replay_id": "store-replay-1",
    }
    audit = FundingClusterStoreAuditReceipt(
        **audit_identity,
        audit_id=deterministic_id("funding_cluster_store_audit", audit_identity),
    )
    verification_identity = {
        "audit_id": audit.audit_id,
        "matches": True,
        "schema_version": "funding_cluster_store_audit_store_verifier.v1",
    }
    verification = FundingClusterStoreAuditStoreVerificationReceipt(
        **verification_identity,
        verification_id=deterministic_id(
            "funding_cluster_store_audit_store_verification", verification_identity
        ),
    )
    chain = build_funding_cluster_audit_chain_receipt(
        audit_receipt=audit,
        verification_receipt=verification,
    )
    assert chain.chain_matches is True
    assert chain.cluster_id == "cluster-1"
    assert chain.chain_id
