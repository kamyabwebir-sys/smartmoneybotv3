from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.adapters.persistence.funding_cluster_audit_chain_store import (
    JsonFundingClusterAuditChainStore,
)
from smart_money.application.funding_cluster_audit_chain import FundingClusterAuditChainReceipt
from smart_money.application.funding_cluster_audit_chain_store_verifier import (
    FundingClusterAuditChainStoreVerificationReceipt,
    verify_funding_cluster_audit_chain_store,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "funding_cluster_audit_chain_recovery_gate.v1"


@dataclass(frozen=True, slots=True)
class FundingClusterAuditChainRecoveryGateReceipt:
    chain_id: str
    verification_id: str
    allowed: bool
    reason: str
    gate_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("chain_id", "verification_id", "reason", "gate_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.allowed, bool):
            raise TypeError("allowed must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported funding cluster audit recovery gate schema_version")
        if self.gate_id != deterministic_id(
            "funding_cluster_audit_chain_recovery_gate", self.identity_payload()
        ):
            raise ValueError("gate_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "chain_id": self.chain_id,
            "reason": self.reason,
            "schema_version": self.schema_version,
            "verification_id": self.verification_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"gate_id": self.gate_id, **self.identity_payload()}


def evaluate_funding_cluster_audit_chain_recovery_gate(
    store: JsonFundingClusterAuditChainStore,
    expected: FundingClusterAuditChainReceipt,
) -> FundingClusterAuditChainRecoveryGateReceipt:
    if not isinstance(store, JsonFundingClusterAuditChainStore):
        raise TypeError("store must be JsonFundingClusterAuditChainStore")
    if not isinstance(expected, FundingClusterAuditChainReceipt):
        raise TypeError("expected must be FundingClusterAuditChainReceipt")
    try:
        verification: FundingClusterAuditChainStoreVerificationReceipt = (
            verify_funding_cluster_audit_chain_store(store, expected)
        )
        allowed = verification.matches
        reason = "verified" if allowed else "replay_mismatch"
        verification_id = verification.verification_id
    except (ValueError, RuntimeError) as exc:
        allowed = False
        reason = f"recovery_blocked:{type(exc).__name__}"
        verification_id = "unverified"
    identity = {
        "allowed": allowed,
        "chain_id": expected.chain_id,
        "reason": reason,
        "schema_version": _SCHEMA_VERSION,
        "verification_id": verification_id,
    }
    return FundingClusterAuditChainRecoveryGateReceipt(
        **identity,
        gate_id=deterministic_id("funding_cluster_audit_chain_recovery_gate", identity),
    )


__all__ = [
    "FundingClusterAuditChainRecoveryGateReceipt",
    "evaluate_funding_cluster_audit_chain_recovery_gate",
]
