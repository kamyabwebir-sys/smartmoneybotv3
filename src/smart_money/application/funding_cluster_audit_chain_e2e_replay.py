from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.adapters.persistence.funding_cluster_audit_chain_final_store import (
    JsonFundingClusterAuditChainFinalStore,
)
from smart_money.application.funding_cluster_audit_chain_final import (
    FundingClusterAuditChainFinalReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "funding_cluster_audit_chain_e2e_replay.v1"


@dataclass(frozen=True, slots=True)
class FundingClusterAuditChainE2EReplayReceipt:
    final_id: str
    matches: bool
    replay_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("final_id", "replay_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported funding cluster e2e replay schema_version")
        if self.replay_id != deterministic_id(
            "funding_cluster_audit_chain_e2e_replay", self.identity_payload()
        ):
            raise ValueError("replay_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "final_id": self.final_id,
            "matches": self.matches,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"replay_id": self.replay_id, **self.identity_payload()}


def replay_funding_cluster_audit_chain_end_to_end(
    store: JsonFundingClusterAuditChainFinalStore,
    expected: FundingClusterAuditChainFinalReceipt,
) -> FundingClusterAuditChainE2EReplayReceipt:
    if not isinstance(store, JsonFundingClusterAuditChainFinalStore):
        raise TypeError("store must be JsonFundingClusterAuditChainFinalStore")
    if not isinstance(expected, FundingClusterAuditChainFinalReceipt):
        raise TypeError("expected must be FundingClusterAuditChainFinalReceipt")
    retained = store.get(expected.final_id)
    matches = retained is not None and retained.canonical_dict() == expected.canonical_dict()
    identity = {
        "final_id": expected.final_id,
        "matches": matches,
        "schema_version": _SCHEMA_VERSION,
    }
    return FundingClusterAuditChainE2EReplayReceipt(
        **identity,
        replay_id=deterministic_id("funding_cluster_audit_chain_e2e_replay", identity),
    )


__all__ = [
    "FundingClusterAuditChainE2EReplayReceipt",
    "replay_funding_cluster_audit_chain_end_to_end",
]
