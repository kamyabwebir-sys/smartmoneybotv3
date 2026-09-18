from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_relationship_intelligence_query_audit import (
    WalletRelationshipIntelligenceQueryAuditReceipt,
)
from smart_money.application.wallet_relationship_intelligence_query_recovery_gate import (
    WalletRelationshipIntelligenceQueryRecoveryGateReceipt,
)
from smart_money.application.wallet_relationship_intelligence_query_audit_store_verifier import (
    WalletRelationshipIntelligenceQueryAuditStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_relationship_intelligence_query_final.v1"


@dataclass(frozen=True, slots=True)
class WalletRelationshipIntelligenceQueryFinalReceipt:
    query_id: str
    audit_id: str
    verification_id: str
    gate_id: str
    accepted: bool
    final_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "query_id",
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
            raise ValueError("unsupported wallet relationship query final schema_version")
        if self.final_id != deterministic_id(
            "wallet_relationship_intelligence_query_final", self.identity_payload()
        ):
            raise ValueError("final_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "audit_id": self.audit_id,
            "gate_id": self.gate_id,
            "query_id": self.query_id,
            "schema_version": self.schema_version,
            "verification_id": self.verification_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"final_id": self.final_id, **self.identity_payload()}


def build_wallet_relationship_intelligence_query_final_receipt(
    *,
    audit_receipt: WalletRelationshipIntelligenceQueryAuditReceipt,
    store_verification: WalletRelationshipIntelligenceQueryAuditStoreVerificationReceipt,
    recovery_gate: WalletRelationshipIntelligenceQueryRecoveryGateReceipt,
) -> WalletRelationshipIntelligenceQueryFinalReceipt:
    if not isinstance(
        audit_receipt, WalletRelationshipIntelligenceQueryAuditReceipt
    ):
        raise TypeError(
            "audit_receipt must be WalletRelationshipIntelligenceQueryAuditReceipt"
        )
    if not isinstance(
        store_verification,
        WalletRelationshipIntelligenceQueryAuditStoreVerificationReceipt,
    ):
        raise TypeError(
            "store_verification must be "
            "WalletRelationshipIntelligenceQueryAuditStoreVerificationReceipt"
        )
    if not isinstance(
        recovery_gate, WalletRelationshipIntelligenceQueryRecoveryGateReceipt
    ):
        raise TypeError(
            "recovery_gate must be WalletRelationshipIntelligenceQueryRecoveryGateReceipt"
        )
    if store_verification.audit_id != audit_receipt.audit_id:
        raise ValueError("store verification audit_id mismatch")
    if recovery_gate.audit_id != audit_receipt.audit_id:
        raise ValueError("recovery gate audit_id mismatch")
    if recovery_gate.query_id != audit_receipt.query_id:
        raise ValueError("recovery gate query_id mismatch")
    identity = {
        "accepted": (
            store_verification.matches
            and recovery_gate.allowed
            and audit_receipt.result_count >= 0
        ),
        "audit_id": audit_receipt.audit_id,
        "gate_id": recovery_gate.gate_id,
        "query_id": audit_receipt.query_id,
        "schema_version": _SCHEMA_VERSION,
        "verification_id": store_verification.verification_id,
    }
    return WalletRelationshipIntelligenceQueryFinalReceipt(
        **identity,
        final_id=deterministic_id(
            "wallet_relationship_intelligence_query_final", identity
        ),
    )


__all__ = [
    "WalletRelationshipIntelligenceQueryFinalReceipt",
    "build_wallet_relationship_intelligence_query_final_receipt",
]
