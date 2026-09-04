from smart_money.application.wallet_relationship_intelligence_query_audit import (
    WalletRelationshipIntelligenceQueryAuditReceipt,
)
from smart_money.application.wallet_relationship_intelligence_query_audit_store_verifier import (
    WalletRelationshipIntelligenceQueryAuditStoreVerificationReceipt,
)
from smart_money.application.wallet_relationship_intelligence_query_recovery_gate import (
    evaluate_wallet_relationship_intelligence_query_recovery_gate,
)
from smart_money.core.ids import deterministic_id


def test_query_recovery_gate_allows_verified_audit() -> None:
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
    gate = evaluate_wallet_relationship_intelligence_query_recovery_gate(
        audit, verification
    )
    assert gate.allowed is True
    assert gate.query_id == audit.query_id
