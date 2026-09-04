from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.funding_cluster_detection import FundingCluster
from smart_money.application.wallet_relationship_evidence import WalletRelationshipEvidence
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "funding_cluster_read_model.v1"


@dataclass(frozen=True, slots=True)
class FundingClusterReadRow:
    cluster: FundingCluster
    relationships: tuple[WalletRelationshipEvidence, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.cluster, FundingCluster):
            raise TypeError("cluster must be FundingCluster")
        if not isinstance(self.relationships, tuple) or not all(
            isinstance(item, WalletRelationshipEvidence) for item in self.relationships
        ):
            raise TypeError("relationships must be a tuple of WalletRelationshipEvidence")
        if tuple(item.relationship_id for item in self.relationships) != self.cluster.relationship_ids:
            raise ValueError("relationships do not match cluster")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "cluster": self.cluster.canonical_dict(),
            "relationships": tuple(item.canonical_dict() for item in self.relationships),
        }


@dataclass(frozen=True, slots=True)
class FundingClusterReadModel:
    rows: tuple[FundingClusterReadRow, ...]
    model_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple) or not all(
            isinstance(item, FundingClusterReadRow) for item in self.rows
        ):
            raise TypeError("rows must be a tuple of FundingClusterReadRow")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported funding cluster read model schema_version")
        expected = deterministic_id(
            "funding_cluster_read_model",
            {"rows": tuple(item.canonical_dict() for item in self.rows), "schema_version": self.schema_version},
        )
        if self.model_id != expected:
            raise ValueError("model_id does not match rows")

    def canonical_dict(self) -> dict[str, Any]:
        return {"model_id": self.model_id, "rows": tuple(item.canonical_dict() for item in self.rows), "schema_version": self.schema_version}


def build_funding_cluster_read_model(
    clusters: tuple[FundingCluster, ...],
    relationships: tuple[WalletRelationshipEvidence, ...],
) -> FundingClusterReadModel:
    if not isinstance(clusters, tuple) or not isinstance(relationships, tuple):
        raise TypeError("clusters and relationships must be tuples")
    relation_map = {item.relationship_id: item for item in relationships}
    rows: list[FundingClusterReadRow] = []
    for cluster in clusters:
        if not isinstance(cluster, FundingCluster):
            raise TypeError("clusters must contain FundingCluster")
        members = tuple(relation_map[item] for item in cluster.relationship_ids if item in relation_map)
        if len(members) != len(cluster.relationship_ids):
            raise ValueError("cluster relationship evidence is incomplete")
        rows.append(FundingClusterReadRow(cluster, members))
    rows.sort(key=lambda item: item.cluster.cluster_id)
    identity = {"rows": tuple(item.canonical_dict() for item in rows), "schema_version": _SCHEMA_VERSION}
    return FundingClusterReadModel(tuple(rows), deterministic_id("funding_cluster_read_model", identity))


__all__ = ["FundingClusterReadModel", "FundingClusterReadRow", "build_funding_cluster_read_model"]
