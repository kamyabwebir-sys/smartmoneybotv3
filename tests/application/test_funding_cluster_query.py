from smart_money.application.funding_cluster_detection import detect_funding_clusters
from smart_money.application.funding_cluster_query import query_funding_clusters
from smart_money.application.funding_cluster_read_model import build_funding_cluster_read_model
from smart_money.application.wallet_relationship_evidence import WalletRelationshipEvidence
from smart_money.core.ids import deterministic_id


def _relationship(source: str, target: str, path: str) -> WalletRelationshipEvidence:
    identity = {
        "edge_evidence_ids": (f"edge-{path}",),
        "path_id": path,
        "provenance": {"source": "funding_graph"},
        "relationship_type": "DIRECT_FUNDING",
        "schema_version": "wallet_relationship_evidence.v1",
        "source_wallet": source,
        "target_wallet": target,
    }
    return WalletRelationshipEvidence(
        **identity,
        relationship_id=deterministic_id("wallet_relationship_evidence", identity),
    )


def test_funding_cluster_query_filters_wallet_size_and_type() -> None:
    relationships = (_relationship("A", "B", "p1"), _relationship("B", "C", "p2"))
    model = build_funding_cluster_read_model(
        detect_funding_clusters(relationships), relationships
    )
    result = query_funding_clusters(
        model, wallet=" B ", min_size=3, max_size=3, relationship_type="DIRECT_FUNDING"
    )
    assert len(result.rows) == 1
    assert result.rows[0].cluster.wallets == ("A", "B", "C")
    assert query_funding_clusters(model, wallet="Z").rows == ()
