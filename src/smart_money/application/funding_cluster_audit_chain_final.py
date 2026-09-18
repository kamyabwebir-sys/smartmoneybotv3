from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.funding_cluster_audit_chain import FundingClusterAuditChainReceipt
from smart_money.application.funding_cluster_audit_chain_recovery_gate import (
    FundingClusterAuditChainRecoveryGateReceipt,
)
from smart_money.application.funding_cluster_audit_chain_store_verifier import (
    FundingClusterAuditChainStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "funding_cluster_audit_chain_final.v1"


@dataclass(frozen=True, slots=True)
class FundingClusterAuditChainFinalReceipt:
    cluster_id: str
    chain_id: str
    store_verification_id: str
    gate_id: str
    accepted: bool
    final_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "cluster_id",
            "chain_id",
            "store_verification_id",
            "gate_id",
            "final_id",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.accepted, bool):
            raise TypeError("accepted must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported funding cluster audit final schema_version")
        if self.final_id != deterministic_id(
            "funding_cluster_audit_chain_final", self.identity_payload()
        ):
            raise ValueError("final_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "chain_id": self.chain_id,
            "cluster_id": self.cluster_id,
            "gate_id": self.gate_id,
            "schema_version": self.schema_version,
            "store_verification_id": self.store_verification_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"final_id": self.final_id, **self.identity_payload()}


def build_funding_cluster_audit_chain_final_receipt(
    *,
    chain_receipt: FundingClusterAuditChainReceipt,
    store_verification: FundingClusterAuditChainStoreVerificationReceipt,
    recovery_gate: FundingClusterAuditChainRecoveryGateReceipt,
) -> FundingClusterAuditChainFinalReceipt:
    if not isinstance(chain_receipt, FundingClusterAuditChainReceipt):
        raise TypeError("chain_receipt must be FundingClusterAuditChainReceipt")
    if not isinstance(store_verification, FundingClusterAuditChainStoreVerificationReceipt):
        raise TypeError("store_verification must be FundingClusterAuditChainStoreVerificationReceipt")
    if not isinstance(recovery_gate, FundingClusterAuditChainRecoveryGateReceipt):
        raise TypeError("recovery_gate must be FundingClusterAuditChainRecoveryGateReceipt")
    if store_verification.chain_id != chain_receipt.chain_id:
        raise ValueError("store verification chain_id mismatch")
    if recovery_gate.chain_id != chain_receipt.chain_id:
        raise ValueError("recovery gate chain_id mismatch")
    identity = {
        "accepted": (
            chain_receipt.chain_matches
            and store_verification.matches
            and recovery_gate.allowed
        ),
        "chain_id": chain_receipt.chain_id,
        "cluster_id": chain_receipt.cluster_id,
        "gate_id": recovery_gate.gate_id,
        "schema_version": _SCHEMA_VERSION,
        "store_verification_id": store_verification.verification_id,
    }
    return FundingClusterAuditChainFinalReceipt(
        **identity,
        final_id=deterministic_id("funding_cluster_audit_chain_final", identity),
    )


__all__ = [
    "FundingClusterAuditChainFinalReceipt",
    "build_funding_cluster_audit_chain_final_receipt",
]
