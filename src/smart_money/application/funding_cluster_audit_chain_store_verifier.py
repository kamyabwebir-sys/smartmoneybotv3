from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.adapters.persistence.funding_cluster_audit_chain_store import (
    JsonFundingClusterAuditChainStore,
)
from smart_money.application.funding_cluster_audit_chain import FundingClusterAuditChainReceipt
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "funding_cluster_audit_chain_store_verifier.v1"


@dataclass(frozen=True, slots=True)
class FundingClusterAuditChainStoreVerificationReceipt:
    chain_id: str
    matches: bool
    verification_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("chain_id", "verification_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported funding cluster audit chain verifier schema_version")
        if self.verification_id != deterministic_id(
            "funding_cluster_audit_chain_store_verification", self.identity_payload()
        ):
            raise ValueError("verification_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "matches": self.matches,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"verification_id": self.verification_id, **self.identity_payload()}


def verify_funding_cluster_audit_chain_store(
    store: JsonFundingClusterAuditChainStore,
    expected: FundingClusterAuditChainReceipt,
) -> FundingClusterAuditChainStoreVerificationReceipt:
    if not isinstance(store, JsonFundingClusterAuditChainStore):
        raise TypeError("store must be JsonFundingClusterAuditChainStore")
    if not isinstance(expected, FundingClusterAuditChainReceipt):
        raise TypeError("expected must be FundingClusterAuditChainReceipt")
    retained = store.get(expected.chain_id)
    if retained is None:
        raise ValueError("expected funding cluster audit chain receipt is missing from Store")
    if retained.canonical_dict() != expected.canonical_dict():
        raise ValueError("stored funding cluster audit chain receipt does not match expected receipt")
    identity = {"chain_id": expected.chain_id, "matches": True, "schema_version": _SCHEMA_VERSION}
    return FundingClusterAuditChainStoreVerificationReceipt(
        **identity,
        verification_id=deterministic_id(
            "funding_cluster_audit_chain_store_verification", identity
        ),
    )


__all__ = [
    "FundingClusterAuditChainStoreVerificationReceipt",
    "verify_funding_cluster_audit_chain_store",
]
