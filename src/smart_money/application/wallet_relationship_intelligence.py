from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.funding_cluster_detection import FundingCluster
from smart_money.application.wallet_relationship_evidence import WalletRelationshipEvidence
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_relationship_intelligence.v1"


@dataclass(frozen=True, slots=True)
class WalletRelationshipIntelligence:
    cluster_id: str
    wallets: tuple[str, ...]
    relationship_ids: tuple[str, ...]
    relationship_count: int
    intelligence_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.cluster_id, str) or not self.cluster_id.strip():
            raise ValueError("cluster_id must be non-empty")
        if not isinstance(self.wallets, tuple) or not self.wallets:
            raise ValueError("wallets must be non-empty tuple")
        if not isinstance(self.relationship_ids, tuple) or not self.relationship_ids:
            raise ValueError("relationship_ids must be non-empty tuple")
        if self.relationship_count != len(self.relationship_ids):
            raise ValueError("relationship_count mismatch")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet relationship intelligence schema_version")
        if self.intelligence_id != deterministic_id(
            "wallet_relationship_intelligence", self.identity_payload()
        ):
            raise ValueError("intelligence_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "relationship_count": self.relationship_count,
            "relationship_ids": self.relationship_ids,
            "schema_version": self.schema_version,
            "wallets": self.wallets,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"intelligence_id": self.intelligence_id, **self.identity_payload()}


def project_wallet_relationship_intelligence(
    cluster: FundingCluster,
    relationships: tuple[WalletRelationshipEvidence, ...],
) -> WalletRelationshipIntelligence:
    if not isinstance(cluster, FundingCluster):
        raise TypeError("cluster must be FundingCluster")
    if not isinstance(relationships, tuple) or not all(
        isinstance(item, WalletRelationshipEvidence) for item in relationships
    ):
        raise TypeError("relationships must be a tuple of WalletRelationshipEvidence")
    selected = tuple(
        sorted(
            (
                item
                for item in relationships
                if item.relationship_id in set(cluster.relationship_ids)
            ),
            key=lambda item: item.relationship_id,
        )
    )
    if tuple(item.relationship_id for item in selected) != cluster.relationship_ids:
        raise ValueError("relationships do not fully cover funding cluster")
    identity = {
        "cluster_id": cluster.cluster_id,
        "relationship_count": len(selected),
        "relationship_ids": cluster.relationship_ids,
        "schema_version": _SCHEMA_VERSION,
        "wallets": cluster.wallets,
    }
    return WalletRelationshipIntelligence(
        **identity,
        intelligence_id=deterministic_id("wallet_relationship_intelligence", identity),
    )


__all__ = [
    "WalletRelationshipIntelligence",
    "project_wallet_relationship_intelligence",
]
