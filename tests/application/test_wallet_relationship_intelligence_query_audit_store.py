from smart_money.adapters.persistence.wallet_relationship_intelligence_query_audit_store import (
    JsonWalletRelationshipIntelligenceQueryAuditStore,
)
from smart_money.application.wallet_relationship_intelligence_query_audit import (
    WalletRelationshipIntelligenceQueryAuditReceipt,
)
from smart_money.core.ids import deterministic_id


def test_wallet_relationship_query_audit_store_round_trip(tmp_path) -> None:
    identity = {
        "parameters": {"wallet": "wallet-a"},
        "query_id": "query-1",
        "result_count": 1,
        "schema_version": "wallet_relationship_intelligence_query_audit.v1",
    }
    receipt = WalletRelationshipIntelligenceQueryAuditReceipt(
        **identity,
        audit_id=deterministic_id(
            "wallet_relationship_intelligence_query_audit", identity
        ),
    )
    path = tmp_path / "query-audit.json"
    store = JsonWalletRelationshipIntelligenceQueryAuditStore(path)
    assert store.append(receipt) == receipt.audit_id
    assert store.append(receipt) == receipt.audit_id
    restored = JsonWalletRelationshipIntelligenceQueryAuditStore(path)
    assert restored.get(receipt.audit_id) == receipt
    assert restored.receipt_count == 1
