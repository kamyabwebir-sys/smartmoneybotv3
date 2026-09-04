from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.wallet_relationship_intelligence import (
    WalletRelationshipIntelligence,
)
from smart_money.application.wallet_relationship_intelligence_ledger import (
    ingest_wallet_relationship_intelligence,
)
from smart_money.application.wallet_relationship_intelligence_read_model import (
    build_wallet_relationship_intelligence_read_model,
)
from smart_money.core.ids import deterministic_id


def test_wallet_relationship_intelligence_read_model() -> None:
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
    ledger = EvidenceGroundingLedger()
    ingest_wallet_relationship_intelligence(model, ledger)
    read_model = build_wallet_relationship_intelligence_read_model(ledger)
    assert len(read_model.rows) == 1
    assert read_model.rows[0].intelligence == model
