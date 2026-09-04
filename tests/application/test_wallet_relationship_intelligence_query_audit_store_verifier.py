from smart_money.adapters.persistence.wallet_relationship_intelligence_query_audit_store import (
    JsonWalletRelationshipIntelligenceQueryAuditStore,
)
from smart_money.application.wallet_relationship_intelligence_query_audit import (
    WalletRelationshipIntelligenceQueryAuditReceipt,
)
from smart_money.application.wallet_relationship_intelligence_query_audit_store_verifier import (
    verify_wallet_relationship_intelligence_query_audit_store,
)
from smart_money.core.ids import deterministic_id


def test_wallet_relationship_query_audit_store_replay_verification(tmp_path) -> None:
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
    store = JsonWalletRelationshipIntelligenceQueryAuditStore(tmp_path / "query-audit.json")
    store.append(receipt)
    verification = verify_wallet_relationship_intelligence_query_audit_store(store, receipt)
    assert verification.matches is True
    assert verification.audit_id == receipt.audit_id
