from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.adapters.persistence.funding_cluster_store_audit_store import (
    JsonFundingClusterStoreAuditStore,
)
from smart_money.application.funding_cluster_store_audit import (
    FundingClusterStoreAuditReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "funding_cluster_store_audit_store_verifier.v1"


@dataclass(frozen=True, slots=True)
class FundingClusterStoreAuditStoreVerificationReceipt:
    audit_id: str
    matches: bool
    verification_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("audit_id", "verification_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported funding cluster store audit verifier schema_version")
        if self.verification_id != deterministic_id(
            "funding_cluster_store_audit_store_verification", self.identity_payload()
        ):
            raise ValueError("verification_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "matches": self.matches,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"verification_id": self.verification_id, **self.identity_payload()}


def verify_funding_cluster_store_audit_store(
    store: JsonFundingClusterStoreAuditStore,
    expected: FundingClusterStoreAuditReceipt,
) -> FundingClusterStoreAuditStoreVerificationReceipt:
    if not isinstance(store, JsonFundingClusterStoreAuditStore):
        raise TypeError("store must be JsonFundingClusterStoreAuditStore")
    if not isinstance(expected, FundingClusterStoreAuditReceipt):
        raise TypeError("expected must be FundingClusterStoreAuditReceipt")
    retained = store.get(expected.audit_id)
    if retained is None:
        raise ValueError("expected funding cluster store audit receipt is missing from Store")
    if retained.canonical_dict() != expected.canonical_dict():
        raise ValueError("stored funding cluster store audit receipt does not match expected receipt")
    identity = {
        "audit_id": expected.audit_id,
        "matches": True,
        "schema_version": _SCHEMA_VERSION,
    }
    return FundingClusterStoreAuditStoreVerificationReceipt(
        **identity,
        verification_id=deterministic_id(
            "funding_cluster_store_audit_store_verification", identity
        ),
    )


__all__ = [
    "FundingClusterStoreAuditStoreVerificationReceipt",
    "verify_funding_cluster_store_audit_store",
]
