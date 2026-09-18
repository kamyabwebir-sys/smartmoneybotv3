from smart_money.application.wallet_relationship_intelligence_audit import (
    WalletRelationshipIntelligenceAuditReceipt,
)
from smart_money.application.wallet_relationship_intelligence_final import (
    build_wallet_relationship_intelligence_final_receipt,
)
from smart_money.application.wallet_relationship_intelligence_recovery_gate import (
    WalletRelationshipIntelligenceRecoveryGateReceipt,
)
from smart_money.application.wallet_relationship_intelligence_store_verifier import (
    WalletRelationshipIntelligenceStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id


def test_wallet_relationship_intelligence_final_receipt() -> None:
    audit_identity = {
        "intelligence_id": "intelligence-1",
        "replay_id": "replay-1",
        "replay_matches": True,
        "schema_version": "wallet_relationship_intelligence_audit.v1",
        "store_verification_id": "verification-1",
    }
    audit = WalletRelationshipIntelligenceAuditReceipt(
        **audit_identity,
        audit_id=deterministic_id("wallet_relationship_intelligence_audit", audit_identity),
    )
    verification_identity = {
        "intelligence_id": audit.intelligence_id,
        "matches": True,
        "schema_version": "wallet_relationship_intelligence_store_verifier.v1",
    }
    verification = WalletRelationshipIntelligenceStoreVerificationReceipt(
        **verification_identity,
        verification_id=deterministic_id(
            "wallet_relationship_intelligence_store_verification", verification_identity
        ),
    )
    gate_identity = {
        "allowed": True,
        "audit_id": audit.audit_id,
        "intelligence_id": audit.intelligence_id,
        "reason": "verified",
        "schema_version": "wallet_relationship_intelligence_recovery_gate.v1",
        "verification_id": verification.verification_id,
    }
    gate = WalletRelationshipIntelligenceRecoveryGateReceipt(
        **gate_identity,
        gate_id=deterministic_id(
            "wallet_relationship_intelligence_recovery_gate", gate_identity
        ),
    )
    final = build_wallet_relationship_intelligence_final_receipt(
        audit_receipt=audit,
        store_verification=verification,
        recovery_gate=gate,
    )
    assert final.accepted is True
    assert final.final_id
