from smart_money.application.wallet_relationship_intelligence_query_audit import (
    WalletRelationshipIntelligenceQueryAuditReceipt,
)
from smart_money.application.wallet_relationship_intelligence_query_final import (
    build_wallet_relationship_intelligence_query_final_receipt,
)
from smart_money.application.wallet_relationship_intelligence_query_recovery_gate import (
    WalletRelationshipIntelligenceQueryRecoveryGateReceipt,
)
from smart_money.application.wallet_relationship_intelligence_query_audit_store_verifier import (
    WalletRelationshipIntelligenceQueryAuditStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id


def test_wallet_relationship_intelligence_query_final_receipt() -> None:
    audit_identity = {
        "parameters": {"wallet": "wallet-a"},
        "query_id": "query-1",
        "result_count": 1,
        "schema_version": "wallet_relationship_intelligence_query_audit.v1",
    }
    audit = WalletRelationshipIntelligenceQueryAuditReceipt(
        **audit_identity,
        audit_id=deterministic_id(
            "wallet_relationship_intelligence_query_audit", audit_identity
        ),
    )
    verification_identity = {
        "audit_id": audit.audit_id,
        "matches": True,
        "schema_version": "wallet_relationship_intelligence_query_audit_store_verifier.v1",
    }
    verification = WalletRelationshipIntelligenceQueryAuditStoreVerificationReceipt(
        **verification_identity,
        verification_id=deterministic_id(
            "wallet_relationship_intelligence_query_audit_store_verification",
            verification_identity,
        ),
    )
    gate_identity = {
        "allowed": True,
        "audit_id": audit.audit_id,
        "query_id": audit.query_id,
        "reason": "verified",
        "schema_version": "wallet_relationship_intelligence_query_recovery_gate.v1",
        "verification_id": verification.verification_id,
    }
    gate = WalletRelationshipIntelligenceQueryRecoveryGateReceipt(
        **gate_identity,
        gate_id=deterministic_id(
            "wallet_relationship_intelligence_query_recovery_gate", gate_identity
        ),
    )
    final = build_wallet_relationship_intelligence_query_final_receipt(
        audit_receipt=audit,
        store_verification=verification,
        recovery_gate=gate,
    )
    assert final.accepted is True
    assert final.query_id == audit.query_id
    assert final.final_id
