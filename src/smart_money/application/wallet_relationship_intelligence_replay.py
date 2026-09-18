from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.funding_cluster_detection import FundingCluster
from smart_money.application.wallet_relationship_evidence import WalletRelationshipEvidence
from smart_money.application.wallet_relationship_intelligence import (
    WalletRelationshipIntelligence,
    project_wallet_relationship_intelligence,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_relationship_intelligence_replay.v1"


@dataclass(frozen=True, slots=True)
class WalletRelationshipIntelligenceReplayReceipt:
    intelligence_id: str
    matches: bool
    replay_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("intelligence_id", "replay_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet relationship intelligence replay schema_version")
        if self.replay_id != deterministic_id(
            "wallet_relationship_intelligence_replay", self.identity_payload()
        ):
            raise ValueError("replay_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "intelligence_id": self.intelligence_id,
            "matches": self.matches,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"replay_id": self.replay_id, **self.identity_payload()}


def replay_verify_wallet_relationship_intelligence(
    cluster: FundingCluster,
    relationships: tuple[WalletRelationshipEvidence, ...],
    expected: WalletRelationshipIntelligence,
) -> WalletRelationshipIntelligenceReplayReceipt:
    if not isinstance(expected, WalletRelationshipIntelligence):
        raise TypeError("expected must be WalletRelationshipIntelligence")
    reconstructed = project_wallet_relationship_intelligence(cluster, relationships)
    matches = reconstructed.canonical_dict() == expected.canonical_dict()
    identity = {
        "intelligence_id": expected.intelligence_id,
        "matches": matches,
        "schema_version": _SCHEMA_VERSION,
    }
    return WalletRelationshipIntelligenceReplayReceipt(
        **identity,
        replay_id=deterministic_id("wallet_relationship_intelligence_replay", identity),
    )


__all__ = [
    "WalletRelationshipIntelligenceReplayReceipt",
    "replay_verify_wallet_relationship_intelligence",
]
