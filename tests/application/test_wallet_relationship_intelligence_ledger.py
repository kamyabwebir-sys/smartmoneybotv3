from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.wallet_relationship_intelligence import (
    WalletRelationshipIntelligence,
)
from smart_money.application.wallet_relationship_intelligence_ledger import (
    ingest_wallet_relationship_intelligence,
)
from smart_money.core.ids import deterministic_id


def test_wallet_relationship_intelligence_ledger_projection(tmp_path) -> None:
    identity = {
        "cluster_id": "cluster-1",
        "relationship_count": 1,
        "relationship_ids": ("relationship-1",),
        "schema_version": "wallet_relationship_intelligence.v1",
        "wallets": ("wallet-a", "wallet-b"),
    }
    intelligence = WalletRelationshipIntelligence(
        **identity,
        intelligence_id=deterministic_id("wallet_relationship_intelligence", identity),
    )
    ledger = EvidenceGroundingLedger()
    evidence_id = ingest_wallet_relationship_intelligence(intelligence, ledger)
    payload = next(iter(ledger.iter_payloads()))
    assert evidence_id == ledger.append(payload)
    assert ledger.get(evidence_id) is not None
