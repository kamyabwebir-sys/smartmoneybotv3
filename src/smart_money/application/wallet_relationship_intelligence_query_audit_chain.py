from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_relationship_intelligence_query_final import (
    WalletRelationshipIntelligenceQueryFinalReceipt,
)
from smart_money.application.wallet_relationship_intelligence_query_final_store_verifier import (
    WalletRelationshipIntelligenceQueryFinalStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_relationship_intelligence_query_audit_chain.v1"


@dataclass(frozen=True, slots=True)
class WalletRelationshipIntelligenceQueryAuditChainReceipt:
    query_id: str
    final_id: str
    verification_id: str
    chain_matches: bool
    chain_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("query_id", "final_id", "verification_id", "chain_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.chain_matches, bool):
            raise TypeError("chain_matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet relationship query audit chain schema_version")
        if self.chain_id != deterministic_id(
            "wallet_relationship_intelligence_query_audit_chain",
            self.identity_payload(),
        ):
            raise ValueError("chain_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "chain_matches": self.chain_matches,
            "final_id": self.final_id,
            "query_id": self.query_id,
            "schema_version": self.schema_version,
            "verification_id": self.verification_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"chain_id": self.chain_id, **self.identity_payload()}


def build_wallet_relationship_intelligence_query_audit_chain_receipt(
    *,
    final_receipt: WalletRelationshipIntelligenceQueryFinalReceipt,
    store_verification: WalletRelationshipIntelligenceQueryFinalStoreVerificationReceipt,
) -> WalletRelationshipIntelligenceQueryAuditChainReceipt:
    if not isinstance(
        final_receipt, WalletRelationshipIntelligenceQueryFinalReceipt
    ):
        raise TypeError(
            "final_receipt must be WalletRelationshipIntelligenceQueryFinalReceipt"
        )
    if not isinstance(
        store_verification,
        WalletRelationshipIntelligenceQueryFinalStoreVerificationReceipt,
    ):
        raise TypeError(
            "store_verification must be "
            "WalletRelationshipIntelligenceQueryFinalStoreVerificationReceipt"
        )
    if store_verification.final_id != final_receipt.final_id:
        raise ValueError("store verification final_id mismatch")
    identity = {
        "chain_matches": final_receipt.accepted and store_verification.matches,
        "final_id": final_receipt.final_id,
        "query_id": final_receipt.query_id,
        "schema_version": _SCHEMA_VERSION,
        "verification_id": store_verification.verification_id,
    }
    return WalletRelationshipIntelligenceQueryAuditChainReceipt(
        **identity,
        chain_id=deterministic_id(
            "wallet_relationship_intelligence_query_audit_chain", identity
        ),
    )


__all__ = [
    "WalletRelationshipIntelligenceQueryAuditChainReceipt",
    "build_wallet_relationship_intelligence_query_audit_chain_receipt",
]
