from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.wallet_relationship_intelligence import (
    WalletRelationshipIntelligence,
)
from smart_money.application.wallet_relationship_intelligence_ledger import (
    ingest_wallet_relationship_intelligence,
)
from smart_money.application.wallet_relationship_intelligence_query import (
    query_wallet_relationship_intelligence,
)
from smart_money.application.wallet_relationship_intelligence_read_model import (
    build_wallet_relationship_intelligence_read_model,
)
from smart_money.core.ids import deterministic_id


def test_wallet_relationship_intelligence_query_filters_wallet_and_cluster() -> None:
    identity = {
        "cluster_id": "cluster-1",
        "relationship_count": 2,
        "relationship_ids": ("relationship-1", "relationship-2"),
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
    result = query_wallet_relationship_intelligence(
        read_model, wallet=" wallet-a ", cluster_id=" cluster-1 ", min_relationship_count=2
    )
    assert len(result.rows) == 1
    assert result.rows[0].intelligence == model
