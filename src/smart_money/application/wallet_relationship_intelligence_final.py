from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_relationship_intelligence_audit import (
    WalletRelationshipIntelligenceAuditReceipt,
)
from smart_money.application.wallet_relationship_intelligence_recovery_gate import (
    WalletRelationshipIntelligenceRecoveryGateReceipt,
)
from smart_money.application.wallet_relationship_intelligence_store_verifier import (
    WalletRelationshipIntelligenceStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_relationship_intelligence_final.v1"


@dataclass(frozen=True, slots=True)
class WalletRelationshipIntelligenceFinalReceipt:
    intelligence_id: str
    audit_id: str
    verification_id: str
    gate_id: str
    accepted: bool
    final_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "intelligence_id",
            "audit_id",
            "verification_id",
            "gate_id",
            "final_id",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.accepted, bool):
            raise TypeError("accepted must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet relationship intelligence final schema_version")
        if self.final_id != deterministic_id(
            "wallet_relationship_intelligence_final", self.identity_payload()
        ):
            raise ValueError("final_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "audit_id": self.audit_id,
            "gate_id": self.gate_id,
            "intelligence_id": self.intelligence_id,
            "schema_version": self.schema_version,
            "verification_id": self.verification_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"final_id": self.final_id, **self.identity_payload()}


def build_wallet_relationship_intelligence_final_receipt(
    *,
    audit_receipt: WalletRelationshipIntelligenceAuditReceipt,
    store_verification: WalletRelationshipIntelligenceStoreVerificationReceipt,
    recovery_gate: WalletRelationshipIntelligenceRecoveryGateReceipt,
) -> WalletRelationshipIntelligenceFinalReceipt:
    if not isinstance(audit_receipt, WalletRelationshipIntelligenceAuditReceipt):
        raise TypeError("audit_receipt must be WalletRelationshipIntelligenceAuditReceipt")
    if not isinstance(store_verification, WalletRelationshipIntelligenceStoreVerificationReceipt):
        raise TypeError("store_verification must be WalletRelationshipIntelligenceStoreVerificationReceipt")
    if not isinstance(recovery_gate, WalletRelationshipIntelligenceRecoveryGateReceipt):
        raise TypeError("recovery_gate must be WalletRelationshipIntelligenceRecoveryGateReceipt")
    if store_verification.intelligence_id != audit_receipt.intelligence_id:
        raise ValueError("store verification intelligence_id mismatch")
    if recovery_gate.intelligence_id != audit_receipt.intelligence_id:
        raise ValueError("recovery gate intelligence_id mismatch")
    identity = {
        "accepted": (
            audit_receipt.replay_matches
            and store_verification.matches
            and recovery_gate.allowed
        ),
        "audit_id": audit_receipt.audit_id,
        "gate_id": recovery_gate.gate_id,
        "intelligence_id": audit_receipt.intelligence_id,
        "schema_version": _SCHEMA_VERSION,
        "verification_id": store_verification.verification_id,
    }
    return WalletRelationshipIntelligenceFinalReceipt(
        **identity,
        final_id=deterministic_id("wallet_relationship_intelligence_final", identity),
    )


__all__ = [
    "WalletRelationshipIntelligenceFinalReceipt",
    "build_wallet_relationship_intelligence_final_receipt",
]
