from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.adapters.persistence.wallet_relationship_intelligence_query_final_store import (
    JsonWalletRelationshipIntelligenceQueryFinalStore,
)
from smart_money.application.wallet_relationship_intelligence_query_final import (
    WalletRelationshipIntelligenceQueryFinalReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_relationship_intelligence_query_final_store_verifier.v1"


@dataclass(frozen=True, slots=True)
class WalletRelationshipIntelligenceQueryFinalStoreVerificationReceipt:
    final_id: str
    matches: bool
    verification_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("final_id", "verification_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError(
                "unsupported wallet relationship query final verifier schema_version"
            )
        if self.verification_id != deterministic_id(
            "wallet_relationship_intelligence_query_final_store_verification",
            self.identity_payload(),
        ):
            raise ValueError("verification_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "final_id": self.final_id,
            "matches": self.matches,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"verification_id": self.verification_id, **self.identity_payload()}


def verify_wallet_relationship_intelligence_query_final_store(
    store: JsonWalletRelationshipIntelligenceQueryFinalStore,
    expected: WalletRelationshipIntelligenceQueryFinalReceipt,
) -> WalletRelationshipIntelligenceQueryFinalStoreVerificationReceipt:
    if not isinstance(store, JsonWalletRelationshipIntelligenceQueryFinalStore):
        raise TypeError(
            "store must be JsonWalletRelationshipIntelligenceQueryFinalStore"
        )
    if not isinstance(expected, WalletRelationshipIntelligenceQueryFinalReceipt):
        raise TypeError(
            "expected must be WalletRelationshipIntelligenceQueryFinalReceipt"
        )
    retained = store.get(expected.final_id)
    if retained is None:
        raise ValueError(
            "expected wallet relationship query final receipt is missing from Store"
        )
    if retained.canonical_dict() != expected.canonical_dict():
        raise ValueError(
            "stored wallet relationship query final receipt does not match expected"
        )
    identity = {
        "final_id": expected.final_id,
        "matches": True,
        "schema_version": _SCHEMA_VERSION,
    }
    return WalletRelationshipIntelligenceQueryFinalStoreVerificationReceipt(
        **identity,
        verification_id=deterministic_id(
            "wallet_relationship_intelligence_query_final_store_verification",
            identity,
        ),
    )


__all__ = [
    "WalletRelationshipIntelligenceQueryFinalStoreVerificationReceipt",
    "verify_wallet_relationship_intelligence_query_final_store",
]
