from smart_money.adapters.persistence.funding_cluster_read_model_store import JsonFundingClusterReadModelStore
from smart_money.application.funding_cluster_detection import detect_funding_clusters
from smart_money.application.funding_cluster_read_model import build_funding_cluster_read_model
from smart_money.application.wallet_relationship_evidence import WalletRelationshipEvidence
from smart_money.core.ids import deterministic_id


def _relationship(source: str, target: str, path: str) -> WalletRelationshipEvidence:
    identity = {"edge_evidence_ids": (f"edge-{path}",), "path_id": path, "provenance": {"source": "funding_graph"}, "relationship_type": "DIRECT_FUNDING", "schema_version": "wallet_relationship_evidence.v1", "source_wallet": source, "target_wallet": target}
    return WalletRelationshipEvidence(**identity, relationship_id=deterministic_id("wallet_relationship_evidence", identity))


def test_funding_cluster_read_model_store_round_trips_idempotently(tmp_path) -> None:
    relationships = (_relationship("A", "B", "p1"), _relationship("B", "C", "p2"))
    model = build_funding_cluster_read_model(detect_funding_clusters(relationships), relationships)
    path = tmp_path / "clusters.json"
    store = JsonFundingClusterReadModelStore(path)
    assert store.save(model) == model.model_id
    assert store.save(model) == model.model_id
    assert JsonFundingClusterReadModelStore(path).load() == model
