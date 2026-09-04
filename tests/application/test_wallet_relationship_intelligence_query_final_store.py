from smart_money.adapters.persistence.wallet_relationship_intelligence_query_final_store import (
    JsonWalletRelationshipIntelligenceQueryFinalStore,
)
from smart_money.application.wallet_relationship_intelligence_query_final import (
    WalletRelationshipIntelligenceQueryFinalReceipt,
)
from smart_money.core.ids import deterministic_id


def test_wallet_relationship_query_final_store_round_trip(tmp_path) -> None:
    identity = {
        "accepted": True,
        "audit_id": "audit-1",
        "gate_id": "gate-1",
        "query_id": "query-1",
        "schema_version": "wallet_relationship_intelligence_query_final.v1",
        "verification_id": "verification-1",
    }
    receipt = WalletRelationshipIntelligenceQueryFinalReceipt(
        **identity,
        final_id=deterministic_id(
            "wallet_relationship_intelligence_query_final", identity
        ),
    )
    path = tmp_path / "query-final.json"
    store = JsonWalletRelationshipIntelligenceQueryFinalStore(path)
    assert store.append(receipt) == receipt.final_id
    assert store.append(receipt) == receipt.final_id
    restored = JsonWalletRelationshipIntelligenceQueryFinalStore(path)
    assert restored.get(receipt.final_id) == receipt
    assert restored.receipt_count == 1
