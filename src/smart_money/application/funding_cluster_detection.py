from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_relationship_evidence import WalletRelationshipEvidence
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "funding_cluster_detection.v1"


@dataclass(frozen=True, slots=True)
class FundingCluster:
    wallets: tuple[str, ...]
    relationship_ids: tuple[str, ...]
    cluster_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.wallets, tuple) or len(self.wallets) < 2:
            raise ValueError("wallets must contain at least two nodes")
        if len(set(self.wallets)) != len(self.wallets):
            raise ValueError("wallets must be unique")
        if not all(isinstance(item, str) and item.strip() for item in self.wallets):
            raise ValueError("wallets must contain non-empty strings")
        if not isinstance(self.relationship_ids, tuple) or not self.relationship_ids:
            raise ValueError("relationship_ids must be non-empty")
        if not all(isinstance(item, str) and item.strip() for item in self.relationship_ids):
            raise ValueError("relationship_ids must contain non-empty strings")
        if not isinstance(self.cluster_id, str) or not self.cluster_id.strip():
            raise ValueError("cluster_id must be non-empty")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported funding cluster schema_version")
        if self.cluster_id != deterministic_id("funding_cluster", self.identity_payload()):
            raise ValueError("cluster_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "relationship_ids": self.relationship_ids,
            "schema_version": self.schema_version,
            "wallets": self.wallets,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"cluster_id": self.cluster_id, **self.identity_payload()}


def detect_funding_clusters(
    relationships: tuple[WalletRelationshipEvidence, ...],
) -> tuple[FundingCluster, ...]:
    if not isinstance(relationships, tuple) or not all(
        isinstance(item, WalletRelationshipEvidence) for item in relationships
    ):
        raise TypeError("relationships must be a tuple of WalletRelationshipEvidence")
    parent: dict[str, str] = {}

    def find(wallet: str) -> str:
        parent.setdefault(wallet, wallet)
        while parent[wallet] != wallet:
            parent[wallet] = parent[parent[wallet]]
            wallet = parent[wallet]
        return wallet

    def union(left: str, right: str) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for relationship in relationships:
        union(relationship.source_wallet, relationship.target_wallet)
    groups: dict[str, list[WalletRelationshipEvidence]] = {}
    for relationship in relationships:
        groups.setdefault(find(relationship.source_wallet), []).append(relationship)
    clusters: list[FundingCluster] = []
    for values in groups.values():
        values.sort(key=lambda item: item.relationship_id)
        wallets = tuple(sorted({item.source_wallet for item in values} | {item.target_wallet for item in values}))
        relationship_ids = tuple(item.relationship_id for item in values)
        identity = {"relationship_ids": relationship_ids, "schema_version": _SCHEMA_VERSION, "wallets": wallets}
        clusters.append(FundingCluster(wallets, relationship_ids, deterministic_id("funding_cluster", identity)))
    return tuple(sorted(clusters, key=lambda item: item.cluster_id))


__all__ = ["FundingCluster", "detect_funding_clusters"]
