from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.adapters.persistence.funding_cluster_replay_store import (
    JsonFundingClusterReplayStore,
)
from smart_money.application.funding_cluster_replay import FundingClusterReplayReceipt
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "funding_cluster_replay_store_verifier.v1"


@dataclass(frozen=True, slots=True)
class FundingClusterReplayStoreVerificationReceipt:
    replay_id: str
    matches: bool
    verification_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("replay_id", "verification_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported funding cluster replay store verifier schema_version")
        if self.verification_id != deterministic_id(
            "funding_cluster_replay_store_verification", self.identity_payload()
        ):
            raise ValueError("verification_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "matches": self.matches,
            "replay_id": self.replay_id,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"verification_id": self.verification_id, **self.identity_payload()}


def verify_funding_cluster_replay_store(
    store: JsonFundingClusterReplayStore,
    expected: FundingClusterReplayReceipt,
) -> FundingClusterReplayStoreVerificationReceipt:
    if not isinstance(store, JsonFundingClusterReplayStore):
        raise TypeError("store must be JsonFundingClusterReplayStore")
    if not isinstance(expected, FundingClusterReplayReceipt):
        raise TypeError("expected must be FundingClusterReplayReceipt")
    retained = store.get(expected.replay_id)
    if retained is None:
        raise ValueError("expected funding cluster replay receipt is missing from Store")
    if retained.canonical_dict() != expected.canonical_dict():
        raise ValueError("stored funding cluster replay receipt does not match expected receipt")
    return FundingClusterReplayStoreVerificationReceipt(
        replay_id=expected.replay_id,
        matches=True,
        verification_id=deterministic_id(
            "funding_cluster_replay_store_verification",
            {
                "matches": True,
                "replay_id": expected.replay_id,
                "schema_version": _SCHEMA_VERSION,
            },
        ),
    )


__all__ = [
    "FundingClusterReplayStoreVerificationReceipt",
    "verify_funding_cluster_replay_store",
]
