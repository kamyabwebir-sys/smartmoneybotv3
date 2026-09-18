from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.adapters.persistence.funding_cluster_read_model_store import (
    JsonFundingClusterReadModelStore,
)
from smart_money.application.funding_cluster_detection import detect_funding_clusters
from smart_money.application.funding_cluster_read_model import build_funding_cluster_read_model
from smart_money.application.wallet_relationship_evidence import WalletRelationshipEvidence
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "funding_cluster_store_replay.v1"


@dataclass(frozen=True, slots=True)
class FundingClusterStoreReplayReceipt:
    model_id: str
    matches: bool
    replay_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("model_id", "replay_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported funding cluster store replay schema_version")
        if self.replay_id != deterministic_id("funding_cluster_store_replay", self.identity_payload()):
            raise ValueError("replay_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "matches": self.matches,
            "model_id": self.model_id,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"replay_id": self.replay_id, **self.identity_payload()}


def replay_verify_funding_cluster_store(
    store: JsonFundingClusterReadModelStore,
    relationships: tuple[WalletRelationshipEvidence, ...],
) -> FundingClusterStoreReplayReceipt:
    if not isinstance(store, JsonFundingClusterReadModelStore):
        raise TypeError("store must be JsonFundingClusterReadModelStore")
    if not isinstance(relationships, tuple) or not all(
        isinstance(item, WalletRelationshipEvidence) for item in relationships
    ):
        raise TypeError("relationships must be a tuple of WalletRelationshipEvidence")
    stored = store.load()
    if stored is None:
        raise ValueError("stored funding cluster read model is missing")
    rebuilt = build_funding_cluster_read_model(
        detect_funding_clusters(relationships), relationships
    )
    if stored.canonical_dict() != rebuilt.canonical_dict():
        raise ValueError("stored funding cluster read model does not match replay")
    return FundingClusterStoreReplayReceipt(
        model_id=stored.model_id,
        matches=True,
        replay_id=deterministic_id(
            "funding_cluster_store_replay",
            {
                "matches": True,
                "model_id": stored.model_id,
                "schema_version": _SCHEMA_VERSION,
            },
        ),
    )


__all__ = ["FundingClusterStoreReplayReceipt", "replay_verify_funding_cluster_store"]
