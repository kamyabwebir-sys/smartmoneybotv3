from smart_money.adapters.persistence.wallet_relationship_intelligence_store import (
    JsonWalletRelationshipIntelligenceStore,
)
from smart_money.application.wallet_relationship_intelligence import (
    WalletRelationshipIntelligence,
)
from smart_money.core.ids import deterministic_id


def test_wallet_relationship_intelligence_store_round_trip(tmp_path) -> None:
    identity = {
        "cluster_id": "cluster-1",
        "relationship_count": 1,
        "relationship_ids": ("relationship-1",),
        "schema_version": "wallet_relationship_intelligence.v1",
        "wallets": ("wallet-a", "wallet-b"),
    }
    model = WalletRelationshipIntelligence(
        **identity,
        intelligence_id=deterministic_id("wallet_relationship_intelligence", identity),
    )
    path = tmp_path / "intelligence.json"
    store = JsonWalletRelationshipIntelligenceStore(path)
    assert store.append(model) == model.intelligence_id
    assert store.append(model) == model.intelligence_id
    restored = JsonWalletRelationshipIntelligenceStore(path)
    assert restored.get(model.intelligence_id) == model
    assert restored.model_count == 1
