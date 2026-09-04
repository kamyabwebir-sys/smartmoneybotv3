from smart_money.application.funding_cluster_audit_chain import FundingClusterAuditChainReceipt
from smart_money.application.funding_cluster_audit_chain_final import (
    build_funding_cluster_audit_chain_final_receipt,
)
from smart_money.application.funding_cluster_audit_chain_recovery_gate import (
    FundingClusterAuditChainRecoveryGateReceipt,
)
from smart_money.application.funding_cluster_audit_chain_store_verifier import (
    FundingClusterAuditChainStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id


def test_funding_cluster_audit_chain_final_receipt_binds_full_chain() -> None:
    chain_identity = {
        "audit_id": "audit-1",
        "chain_matches": True,
        "cluster_id": "cluster-1",
        "schema_version": "funding_cluster_audit_chain.v1",
        "verification_id": "verification-1",
    }
    chain = FundingClusterAuditChainReceipt(
        **chain_identity,
        chain_id=deterministic_id("funding_cluster_audit_chain", chain_identity),
    )
    verification_identity = {
        "chain_id": chain.chain_id,
        "matches": True,
        "schema_version": "funding_cluster_audit_chain_store_verifier.v1",
    }
    verification = FundingClusterAuditChainStoreVerificationReceipt(
        **verification_identity,
        verification_id=deterministic_id(
            "funding_cluster_audit_chain_store_verification", verification_identity
        ),
    )
    gate_identity = {
        "allowed": True,
        "chain_id": chain.chain_id,
        "reason": "verified",
        "schema_version": "funding_cluster_audit_chain_recovery_gate.v1",
        "verification_id": verification.verification_id,
    }
    gate = FundingClusterAuditChainRecoveryGateReceipt(
        **gate_identity,
        gate_id=deterministic_id("funding_cluster_audit_chain_recovery_gate", gate_identity),
    )
    final = build_funding_cluster_audit_chain_final_receipt(
        chain_receipt=chain,
        store_verification=verification,
        recovery_gate=gate,
    )
    assert final.accepted is True
    assert final.cluster_id == "cluster-1"
    assert final.final_id
