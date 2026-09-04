from smart_money.application.funding_cluster_detection import detect_funding_clusters
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


def test_funding_clusters_find_connected_wallet_components() -> None:
    relationships = (_relationship("A", "B", "p1"), _relationship("B", "C", "p2"), _relationship("X", "Y", "p3"))
    clusters = detect_funding_clusters(tuple(reversed(relationships)))
    assert len(clusters) == 2
    assert ("A", "B", "C") in tuple(item.wallets for item in clusters)
    assert detect_funding_clusters(relationships) == clusters
