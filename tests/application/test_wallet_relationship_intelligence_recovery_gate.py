from smart_money.application.wallet_relationship_intelligence_audit import (
    WalletRelationshipIntelligenceAuditReceipt,
)
from smart_money.application.wallet_relationship_intelligence_audit_store_verifier import (
    WalletRelationshipIntelligenceAuditStoreVerificationReceipt,
)
from smart_money.application.wallet_relationship_intelligence_recovery_gate import (
    evaluate_wallet_relationship_intelligence_recovery_gate,
)
from smart_money.core.ids import deterministic_id


def _audit() -> WalletRelationshipIntelligenceAuditReceipt:
    identity = {
        "intelligence_id": "intelligence-1",
        "replay_id": "replay-1",
        "replay_matches": True,
        "schema_version": "wallet_relationship_intelligence_audit.v1",
        "store_verification_id": "verification-1",
    }
    return WalletRelationshipIntelligenceAuditReceipt(
        **identity,
        audit_id=deterministic_id("wallet_relationship_intelligence_audit", identity),
    )


def test_recovery_gate_allows_verified_audit() -> None:
    audit = _audit()
    identity = {
        "audit_id": audit.audit_id,
        "matches": True,
        "schema_version": "wallet_relationship_intelligence_audit_store_verifier.v1",
    }
    verification = WalletRelationshipIntelligenceAuditStoreVerificationReceipt(
        **identity,
        verification_id=deterministic_id(
            "wallet_relationship_intelligence_audit_store_verification", identity
        ),
    )
    gate = evaluate_wallet_relationship_intelligence_recovery_gate(audit, verification)
    assert gate.allowed is True
    assert gate.reason == "verified"
