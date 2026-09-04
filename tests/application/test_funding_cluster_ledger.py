from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.funding_cluster_detection import FundingCluster
from smart_money.application.funding_cluster_ledger import ingest_funding_cluster
from smart_money.core.ids import deterministic_id


def test_funding_cluster_projects_idempotently_with_relationship_linkage() -> None:
    identity = {
        "relationship_ids": ("r1", "r2"),
        "schema_version": "funding_cluster_detection.v1",
        "wallets": ("A", "B", "C"),
    }
    cluster = FundingCluster(
        wallets=("A", "B", "C"),
        relationship_ids=("r1", "r2"),
        cluster_id=deterministic_id("funding_cluster", identity),
    )
    ledger = EvidenceGroundingLedger()
    first = ingest_funding_cluster(cluster, ledger)
    second = ingest_funding_cluster(cluster, ledger)
    payload = ledger.get(first.evidence_id)
    assert payload is not None
    assert payload.evidence_type == "funding_cluster"
    assert payload.data["funding_cluster"]["cluster_id"] == cluster.cluster_id
    assert tuple(payload.data["funding_cluster"]["relationship_ids"]) == cluster.relationship_ids
    assert second.already_present is True
