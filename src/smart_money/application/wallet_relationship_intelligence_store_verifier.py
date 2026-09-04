from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.adapters.persistence.wallet_relationship_intelligence_store import (
    JsonWalletRelationshipIntelligenceStore,
)
from smart_money.application.wallet_relationship_intelligence import (
    WalletRelationshipIntelligence,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_relationship_intelligence_store_verifier.v1"


@dataclass(frozen=True, slots=True)
class WalletRelationshipIntelligenceStoreVerificationReceipt:
    intelligence_id: str
    matches: bool
    verification_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("intelligence_id", "verification_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet relationship intelligence store verifier schema_version")
        if self.verification_id != deterministic_id(
            "wallet_relationship_intelligence_store_verification", self.identity_payload()
        ):
            raise ValueError("verification_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "intelligence_id": self.intelligence_id,
            "matches": self.matches,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"verification_id": self.verification_id, **self.identity_payload()}


def verify_wallet_relationship_intelligence_store(
    store: JsonWalletRelationshipIntelligenceStore,
    expected: WalletRelationshipIntelligence,
) -> WalletRelationshipIntelligenceStoreVerificationReceipt:
    if not isinstance(store, JsonWalletRelationshipIntelligenceStore):
        raise TypeError("store must be JsonWalletRelationshipIntelligenceStore")
    if not isinstance(expected, WalletRelationshipIntelligence):
        raise TypeError("expected must be WalletRelationshipIntelligence")
    retained = store.get(expected.intelligence_id)
    if retained is None:
        raise ValueError("expected wallet relationship intelligence is missing from Store")
    if retained.canonical_dict() != expected.canonical_dict():
        raise ValueError("stored wallet relationship intelligence does not match expected model")
    identity = {
        "intelligence_id": expected.intelligence_id,
        "matches": True,
        "schema_version": _SCHEMA_VERSION,
    }
    return WalletRelationshipIntelligenceStoreVerificationReceipt(
        **identity,
        verification_id=deterministic_id(
            "wallet_relationship_intelligence_store_verification", identity
        ),
    )


__all__ = [
    "WalletRelationshipIntelligenceStoreVerificationReceipt",
    "verify_wallet_relationship_intelligence_store",
]
