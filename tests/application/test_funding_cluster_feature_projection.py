from smart_money.application.funding_cluster_detection import detect_funding_clusters
from smart_money.application.funding_cluster_feature_projection import (
    project_funding_cluster_features,
)
from smart_money.application.wallet_relationship_evidence import WalletRelationshipEvidence
from smart_money.core.ids import deterministic_id


def test_project_funding_cluster_features() -> None:
    identity = {
        "edge_evidence_ids": ("edge-1",),
        "path_id": "path-1",
        "provenance": {"source": "test"},
        "relationship_type": "DIRECT_FUNDING",
        "schema_version": "wallet_relationship_evidence.v1",
        "source_wallet": "wallet-a",
        "target_wallet": "wallet-b",
    }
    relationship = WalletRelationshipEvidence(
        **identity,
        relationship_id=deterministic_id("wallet_relationship_evidence", identity),
    )
    cluster = detect_funding_clusters((relationship,))[0]
    features = project_funding_cluster_features(
        cluster,
        profile_ids={"wallet-a": "profile-a", "wallet-b": "profile-b"},
        cohort_count=1,
    )
    assert len(features) == 2
    assert all(feature.relationship_count == 1 for feature in features)
