from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.funding_cluster_detection import FundingCluster, detect_funding_clusters
from smart_money.application.funding_cluster_read_model import FundingClusterReadModel, build_funding_cluster_read_model
from smart_money.application.wallet_relationship_evidence import WalletRelationshipEvidence
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "funding_cluster_replay_integration.v1"


@dataclass(frozen=True, slots=True)
class FundingClusterReplayIntegrationReceipt:
    cluster_id: str
    read_model_id: str
    matches: bool
    integration_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("cluster_id", "read_model_id", "integration_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported funding cluster replay integration schema_version")
        if self.integration_id != deterministic_id("funding_cluster_replay_integration", self.identity_payload()):
            raise ValueError("integration_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {"cluster_id": self.cluster_id, "matches": self.matches, "read_model_id": self.read_model_id, "schema_version": self.schema_version}

    def canonical_dict(self) -> dict[str, Any]:
        return {"integration_id": self.integration_id, **self.identity_payload()}


def replay_integrate_funding_cluster(
    expected: FundingCluster,
    relationships: tuple[WalletRelationshipEvidence, ...],
) -> tuple[FundingClusterReadModel, FundingClusterReplayIntegrationReceipt]:
    if not isinstance(expected, FundingCluster):
        raise TypeError("expected must be FundingCluster")
    if not isinstance(relationships, tuple) or not all(isinstance(item, WalletRelationshipEvidence) for item in relationships):
        raise TypeError("relationships must be a tuple of WalletRelationshipEvidence")
    rebuilt = next((item for item in detect_funding_clusters(relationships) if item.cluster_id == expected.cluster_id), None)
    if rebuilt is None or rebuilt.canonical_dict() != expected.canonical_dict():
        raise ValueError("funding cluster replay integration mismatch")
    model = build_funding_cluster_read_model((rebuilt,), relationships)
    identity = {"cluster_id": rebuilt.cluster_id, "matches": True, "read_model_id": model.model_id, "schema_version": _SCHEMA_VERSION}
    return model, FundingClusterReplayIntegrationReceipt(**identity, integration_id=deterministic_id("funding_cluster_replay_integration", identity))


__all__ = ["FundingClusterReplayIntegrationReceipt", "replay_integrate_funding_cluster"]
