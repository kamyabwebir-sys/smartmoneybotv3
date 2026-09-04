from smart_money.application.funding_cluster_detection import detect_funding_clusters
from smart_money.application.wallet_relationship_evidence import WalletRelationshipEvidence
from smart_money.application.wallet_relationship_intelligence import (
    project_wallet_relationship_intelligence,
)
from smart_money.core.ids import deterministic_id


def test_project_wallet_relationship_intelligence() -> None:
    identity = {
        "edge_evidence_ids": ("edge-1",),
        "path_id": "path-1",
        "provenance": {"source": "test"},
        "relationship_type": "DIRECT_FUNDING",
        "schema_version": "wallet_relationship_evidence.v1",
        "source_wallet": "wallet-a",
        "target_wallet": "wallet-b",
    }
    relationships = (WalletRelationshipEvidence(
        **identity,
        relationship_id=deterministic_id("wallet_relationship_evidence", identity),
    ),)
    cluster = detect_funding_clusters(relationships)[0]
    projection = project_wallet_relationship_intelligence(cluster, relationships)
    assert projection.cluster_id == cluster.cluster_id
    assert projection.relationship_count == 1
    assert projection.intelligence_id
