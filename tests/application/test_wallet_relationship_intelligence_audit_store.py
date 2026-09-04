from smart_money.adapters.persistence.wallet_relationship_intelligence_audit_store import (
    JsonWalletRelationshipIntelligenceAuditStore,
)
from smart_money.application.wallet_relationship_intelligence_audit import (
    WalletRelationshipIntelligenceAuditReceipt,
)
from smart_money.core.ids import deterministic_id


def test_wallet_relationship_intelligence_audit_store_round_trip(tmp_path) -> None:
    identity = {
        "intelligence_id": "intelligence-1",
        "replay_id": "replay-1",
        "replay_matches": True,
        "schema_version": "wallet_relationship_intelligence_audit.v1",
        "store_verification_id": "verification-1",
    }
    receipt = WalletRelationshipIntelligenceAuditReceipt(
        **identity,
        audit_id=deterministic_id("wallet_relationship_intelligence_audit", identity),
    )
    path = tmp_path / "audit.json"
    store = JsonWalletRelationshipIntelligenceAuditStore(path)
    assert store.append(receipt) == receipt.audit_id
    assert store.append(receipt) == receipt.audit_id
    restored = JsonWalletRelationshipIntelligenceAuditStore(path)
    assert restored.get(receipt.audit_id) == receipt
    assert restored.receipt_count == 1
