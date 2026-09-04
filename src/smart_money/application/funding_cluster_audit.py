from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.funding_cluster_ledger import FundingClusterLedgerReceipt
from smart_money.application.funding_cluster_replay import FundingClusterReplayReceipt
from smart_money.application.funding_cluster_replay_store_verifier import (
    FundingClusterReplayStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "funding_cluster_audit.v1"


@dataclass(frozen=True, slots=True)
class FundingClusterAuditReceipt:
    cluster_id: str
    ledger_receipt_id: str
    replay_id: str
    store_verification_id: str
    replay_matches: bool
    audit_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "cluster_id",
            "ledger_receipt_id",
            "replay_id",
            "store_verification_id",
            "audit_id",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.replay_matches, bool):
            raise TypeError("replay_matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported funding cluster audit schema_version")
        if self.audit_id != deterministic_id("funding_cluster_audit", self.identity_payload()):
            raise ValueError("audit_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "ledger_receipt_id": self.ledger_receipt_id,
            "replay_id": self.replay_id,
            "replay_matches": self.replay_matches,
            "schema_version": self.schema_version,
            "store_verification_id": self.store_verification_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"audit_id": self.audit_id, **self.identity_payload()}


def build_funding_cluster_audit_receipt(
    *,
    cluster_id: str,
    ledger_receipt: FundingClusterLedgerReceipt,
    replay_receipt: FundingClusterReplayReceipt,
    store_verification: FundingClusterReplayStoreVerificationReceipt,
) -> FundingClusterAuditReceipt:
    if not isinstance(cluster_id, str) or not cluster_id.strip():
        raise ValueError("cluster_id must be non-empty")
    if not isinstance(ledger_receipt, FundingClusterLedgerReceipt):
        raise TypeError("ledger_receipt must be FundingClusterLedgerReceipt")
    if not isinstance(replay_receipt, FundingClusterReplayReceipt):
        raise TypeError("replay_receipt must be FundingClusterReplayReceipt")
    if not isinstance(store_verification, FundingClusterReplayStoreVerificationReceipt):
        raise TypeError(
            "store_verification must be FundingClusterReplayStoreVerificationReceipt"
        )
    normalized = cluster_id.strip()
    if ledger_receipt.cluster_id != normalized:
        raise ValueError("ledger receipt cluster_id mismatch")
    if replay_receipt.cluster_id != normalized:
        raise ValueError("replay receipt cluster_id mismatch")
    if store_verification.replay_id != replay_receipt.replay_id:
        raise ValueError("store verification replay_id mismatch")
    identity = {
        "cluster_id": normalized,
        "ledger_receipt_id": ledger_receipt.receipt_id,
        "replay_id": replay_receipt.replay_id,
        "replay_matches": replay_receipt.matches and store_verification.matches,
        "schema_version": _SCHEMA_VERSION,
        "store_verification_id": store_verification.verification_id,
    }
    return FundingClusterAuditReceipt(
        **identity,
        audit_id=deterministic_id("funding_cluster_audit", identity),
    )


__all__ = ["FundingClusterAuditReceipt", "build_funding_cluster_audit_receipt"]
