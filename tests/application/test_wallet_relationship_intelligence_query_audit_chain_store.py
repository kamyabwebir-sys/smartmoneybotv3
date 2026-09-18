from smart_money.adapters.persistence.wallet_relationship_intelligence_query_audit_chain_store import (
    JsonWalletRelationshipIntelligenceQueryAuditChainStore,
)
from smart_money.application.wallet_relationship_intelligence_query_audit_chain import (
    WalletRelationshipIntelligenceQueryAuditChainReceipt,
)
from smart_money.core.ids import deterministic_id


def test_wallet_relationship_query_audit_chain_store_round_trip(tmp_path) -> None:
    identity = {
        "chain_matches": True,
        "final_id": "final-1",
        "query_id": "query-1",
        "schema_version": "wallet_relationship_intelligence_query_audit_chain.v1",
        "verification_id": "verification-1",
    }
    receipt = WalletRelationshipIntelligenceQueryAuditChainReceipt(
        **identity,
        chain_id=deterministic_id(
            "wallet_relationship_intelligence_query_audit_chain", identity
        ),
    )
    path = tmp_path / "query-audit-chain.json"
    store = JsonWalletRelationshipIntelligenceQueryAuditChainStore(path)
    assert store.append(receipt) == receipt.chain_id
    assert store.append(receipt) == receipt.chain_id
    restored = JsonWalletRelationshipIntelligenceQueryAuditChainStore(path)
    assert restored.get(receipt.chain_id) == receipt
    assert restored.receipt_count == 1
