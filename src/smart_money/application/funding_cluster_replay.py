from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.funding_cluster_detection import (
    FundingCluster,
    detect_funding_clusters,
)
from smart_money.application.wallet_relationship_evidence import WalletRelationshipEvidence
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "funding_cluster_replay.v1"


@dataclass(frozen=True, slots=True)
class FundingClusterReplayReceipt:
    cluster_id: str
    matches: bool
    replay_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("cluster_id", "replay_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported funding cluster replay schema_version")
        if self.replay_id != deterministic_id("funding_cluster_replay", self.identity_payload()):
            raise ValueError("replay_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "matches": self.matches,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"replay_id": self.replay_id, **self.identity_payload()}


def replay_verify_funding_cluster(
    expected: FundingCluster,
    relationships: tuple[WalletRelationshipEvidence, ...],
) -> FundingClusterReplayReceipt:
    if not isinstance(expected, FundingCluster):
        raise TypeError("expected must be FundingCluster")
    if not isinstance(relationships, tuple) or not all(
        isinstance(item, WalletRelationshipEvidence) for item in relationships
    ):
        raise TypeError("relationships must be a tuple of WalletRelationshipEvidence")
    rebuilt = next(
        (
            item
            for item in detect_funding_clusters(relationships)
            if item.cluster_id == expected.cluster_id
        ),
        None,
    )
    if rebuilt is None or rebuilt.canonical_dict() != expected.canonical_dict():
        raise ValueError("funding cluster replay does not match expected cluster")
    return FundingClusterReplayReceipt(
        cluster_id=expected.cluster_id,
        matches=True,
        replay_id=deterministic_id(
            "funding_cluster_replay",
            {
                "cluster_id": expected.cluster_id,
                "matches": True,
                "schema_version": _SCHEMA_VERSION,
            },
        ),
    )


__all__ = ["FundingClusterReplayReceipt", "replay_verify_funding_cluster"]
