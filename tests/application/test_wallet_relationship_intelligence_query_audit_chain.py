from smart_money.application.wallet_relationship_intelligence_query_audit_chain import (
    build_wallet_relationship_intelligence_query_audit_chain_receipt,
)
from smart_money.application.wallet_relationship_intelligence_query_final import (
    WalletRelationshipIntelligenceQueryFinalReceipt,
)
from smart_money.application.wallet_relationship_intelligence_query_final_store_verifier import (
    WalletRelationshipIntelligenceQueryFinalStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id


def test_wallet_relationship_query_audit_chain_integration() -> None:
    final_identity = {
        "accepted": True,
        "audit_id": "audit-1",
        "gate_id": "gate-1",
        "query_id": "query-1",
        "schema_version": "wallet_relationship_intelligence_query_final.v1",
        "verification_id": "verification-1",
    }
    final = WalletRelationshipIntelligenceQueryFinalReceipt(
        **final_identity,
        final_id=deterministic_id(
            "wallet_relationship_intelligence_query_final", final_identity
        ),
    )
    verification_identity = {
        "final_id": final.final_id,
        "matches": True,
        "schema_version": "wallet_relationship_intelligence_query_final_store_verifier.v1",
    }
    verification = WalletRelationshipIntelligenceQueryFinalStoreVerificationReceipt(
        **verification_identity,
        verification_id=deterministic_id(
            "wallet_relationship_intelligence_query_final_store_verification",
            verification_identity,
        ),
    )
    chain = build_wallet_relationship_intelligence_query_audit_chain_receipt(
        final_receipt=final,
        store_verification=verification,
    )
    assert chain.chain_matches is True
    assert chain.query_id == final.query_id
    assert chain.chain_id
