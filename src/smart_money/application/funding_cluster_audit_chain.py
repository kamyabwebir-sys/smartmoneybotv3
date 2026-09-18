from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.funding_cluster_store_audit import (
    FundingClusterStoreAuditReceipt,
)
from smart_money.application.funding_cluster_store_audit_store_verifier import (
    FundingClusterStoreAuditStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "funding_cluster_audit_chain.v1"


@dataclass(frozen=True, slots=True)
class FundingClusterAuditChainReceipt:
    cluster_id: str
    audit_id: str
    verification_id: str
    chain_id: str
    chain_matches: bool
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("cluster_id", "audit_id", "verification_id", "chain_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.chain_matches, bool):
            raise TypeError("chain_matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported funding cluster audit chain schema_version")
        if self.chain_id != deterministic_id("funding_cluster_audit_chain", self.identity_payload()):
            raise ValueError("chain_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "chain_matches": self.chain_matches,
            "cluster_id": self.cluster_id,
            "schema_version": self.schema_version,
            "verification_id": self.verification_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"chain_id": self.chain_id, **self.identity_payload()}


def build_funding_cluster_audit_chain_receipt(
    *,
    audit_receipt: FundingClusterStoreAuditReceipt,
    verification_receipt: FundingClusterStoreAuditStoreVerificationReceipt,
) -> FundingClusterAuditChainReceipt:
    if not isinstance(audit_receipt, FundingClusterStoreAuditReceipt):
        raise TypeError("audit_receipt must be FundingClusterStoreAuditReceipt")
    if not isinstance(
        verification_receipt, FundingClusterStoreAuditStoreVerificationReceipt
    ):
        raise TypeError(
            "verification_receipt must be FundingClusterStoreAuditStoreVerificationReceipt"
        )
    if verification_receipt.audit_id != audit_receipt.audit_id:
        raise ValueError("verification receipt audit_id mismatch")
    identity = {
        "audit_id": audit_receipt.audit_id,
        "chain_matches": verification_receipt.matches and audit_receipt.replay_matches,
        "cluster_id": audit_receipt.cluster_id,
        "schema_version": _SCHEMA_VERSION,
        "verification_id": verification_receipt.verification_id,
    }
    return FundingClusterAuditChainReceipt(
        **identity,
        chain_id=deterministic_id("funding_cluster_audit_chain", identity),
    )


__all__ = [
    "FundingClusterAuditChainReceipt",
    "build_funding_cluster_audit_chain_receipt",
]
