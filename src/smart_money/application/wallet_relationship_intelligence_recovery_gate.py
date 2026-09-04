from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_relationship_intelligence_audit import (
    WalletRelationshipIntelligenceAuditReceipt,
)
from smart_money.application.wallet_relationship_intelligence_audit_store_verifier import (
    WalletRelationshipIntelligenceAuditStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_relationship_intelligence_recovery_gate.v1"


@dataclass(frozen=True, slots=True)
class WalletRelationshipIntelligenceRecoveryGateReceipt:
    intelligence_id: str
    audit_id: str
    verification_id: str
    allowed: bool
    reason: str
    gate_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "intelligence_id",
            "audit_id",
            "verification_id",
            "reason",
            "gate_id",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.allowed, bool):
            raise TypeError("allowed must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet relationship recovery gate schema_version")
        if self.gate_id != deterministic_id(
            "wallet_relationship_intelligence_recovery_gate", self.identity_payload()
        ):
            raise ValueError("gate_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "audit_id": self.audit_id,
            "intelligence_id": self.intelligence_id,
            "reason": self.reason,
            "schema_version": self.schema_version,
            "verification_id": self.verification_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"gate_id": self.gate_id, **self.identity_payload()}


def evaluate_wallet_relationship_intelligence_recovery_gate(
    audit_receipt: WalletRelationshipIntelligenceAuditReceipt,
    verification_receipt: WalletRelationshipIntelligenceAuditStoreVerificationReceipt,
) -> WalletRelationshipIntelligenceRecoveryGateReceipt:
    if not isinstance(audit_receipt, WalletRelationshipIntelligenceAuditReceipt):
        raise TypeError("audit_receipt must be WalletRelationshipIntelligenceAuditReceipt")
    if not isinstance(
        verification_receipt, WalletRelationshipIntelligenceAuditStoreVerificationReceipt
    ):
        raise TypeError(
            "verification_receipt must be WalletRelationshipIntelligenceAuditStoreVerificationReceipt"
        )
    if verification_receipt.audit_id != audit_receipt.audit_id:
        raise ValueError("verification receipt audit_id mismatch")
    allowed = audit_receipt.replay_matches and verification_receipt.matches
    reason = "verified" if allowed else "recovery_blocked:verification_mismatch"
    identity = {
        "allowed": allowed,
        "audit_id": audit_receipt.audit_id,
        "intelligence_id": audit_receipt.intelligence_id,
        "reason": reason,
        "schema_version": _SCHEMA_VERSION,
        "verification_id": verification_receipt.verification_id,
    }
    return WalletRelationshipIntelligenceRecoveryGateReceipt(
        **identity,
        gate_id=deterministic_id(
            "wallet_relationship_intelligence_recovery_gate", identity
        ),
    )


__all__ = [
    "WalletRelationshipIntelligenceRecoveryGateReceipt",
    "evaluate_wallet_relationship_intelligence_recovery_gate",
]
