from smart_money.adapters.persistence.wallet_relationship_intelligence_store import (
    JsonWalletRelationshipIntelligenceStore,
)
from smart_money.application.wallet_relationship_intelligence import (
    WalletRelationshipIntelligence,
)
from smart_money.application.wallet_relationship_intelligence_store_verifier import (
    verify_wallet_relationship_intelligence_store,
)
from smart_money.core.ids import deterministic_id


def test_wallet_relationship_intelligence_store_replay_verification(tmp_path) -> None:
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
    store = JsonWalletRelationshipIntelligenceStore(tmp_path / "intelligence.json")
    store.append(model)
    verification = verify_wallet_relationship_intelligence_store(store, model)
    assert verification.matches is True
    assert verification.intelligence_id == model.intelligence_id
