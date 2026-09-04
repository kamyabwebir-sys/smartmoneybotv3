from smart_money.adapters.persistence.wallet_relationship_intelligence_final_store import (
    JsonWalletRelationshipIntelligenceFinalStore,
)
from smart_money.application.wallet_relationship_intelligence_final import (
    WalletRelationshipIntelligenceFinalReceipt,
)
from smart_money.core.ids import deterministic_id


def test_wallet_relationship_intelligence_final_store_round_trip(tmp_path) -> None:
    identity = {
        "accepted": True,
        "audit_id": "audit-1",
        "gate_id": "gate-1",
        "intelligence_id": "intelligence-1",
        "schema_version": "wallet_relationship_intelligence_final.v1",
        "verification_id": "verification-1",
    }
    receipt = WalletRelationshipIntelligenceFinalReceipt(
        **identity,
        final_id=deterministic_id("wallet_relationship_intelligence_final", identity),
    )
    path = tmp_path / "final.json"
    store = JsonWalletRelationshipIntelligenceFinalStore(path)
    assert store.append(receipt) == receipt.final_id
    assert store.append(receipt) == receipt.final_id
    restored = JsonWalletRelationshipIntelligenceFinalStore(path)
    assert restored.get(receipt.final_id) == receipt
    assert restored.receipt_count == 1
