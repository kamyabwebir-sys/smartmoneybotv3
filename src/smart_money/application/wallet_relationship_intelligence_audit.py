from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_relationship_intelligence_replay import (
    WalletRelationshipIntelligenceReplayReceipt,
)
from smart_money.application.wallet_relationship_intelligence_store_verifier import (
    WalletRelationshipIntelligenceStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_relationship_intelligence_audit.v1"


@dataclass(frozen=True, slots=True)
class WalletRelationshipIntelligenceAuditReceipt:
    intelligence_id: str
    replay_id: str
    store_verification_id: str
    replay_matches: bool
    audit_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "intelligence_id",
            "replay_id",
            "store_verification_id",
            "audit_id",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.replay_matches, bool):
            raise TypeError("replay_matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet relationship intelligence audit schema_version")
        if self.audit_id != deterministic_id(
            "wallet_relationship_intelligence_audit", self.identity_payload()
        ):
            raise ValueError("audit_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "intelligence_id": self.intelligence_id,
            "replay_id": self.replay_id,
            "replay_matches": self.replay_matches,
            "schema_version": self.schema_version,
            "store_verification_id": self.store_verification_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"audit_id": self.audit_id, **self.identity_payload()}


def build_wallet_relationship_intelligence_audit_receipt(
    *,
    intelligence_id: str,
    replay_receipt: WalletRelationshipIntelligenceReplayReceipt,
    store_verification: WalletRelationshipIntelligenceStoreVerificationReceipt,
) -> WalletRelationshipIntelligenceAuditReceipt:
    if not isinstance(intelligence_id, str) or not intelligence_id.strip():
        raise ValueError("intelligence_id must be non-empty")
    if not isinstance(replay_receipt, WalletRelationshipIntelligenceReplayReceipt):
        raise TypeError("replay_receipt must be WalletRelationshipIntelligenceReplayReceipt")
    if not isinstance(
        store_verification, WalletRelationshipIntelligenceStoreVerificationReceipt
    ):
        raise TypeError(
            "store_verification must be WalletRelationshipIntelligenceStoreVerificationReceipt"
        )
    normalized = intelligence_id.strip()
    if replay_receipt.intelligence_id != normalized:
        raise ValueError("replay receipt intelligence_id mismatch")
    if store_verification.intelligence_id != normalized:
        raise ValueError("store verification intelligence_id mismatch")
    identity = {
        "intelligence_id": normalized,
        "replay_id": replay_receipt.replay_id,
        "replay_matches": replay_receipt.matches and store_verification.matches,
        "schema_version": _SCHEMA_VERSION,
        "store_verification_id": store_verification.verification_id,
    }
    return WalletRelationshipIntelligenceAuditReceipt(
        **identity,
        audit_id=deterministic_id("wallet_relationship_intelligence_audit", identity),
    )


__all__ = [
    "WalletRelationshipIntelligenceAuditReceipt",
    "build_wallet_relationship_intelligence_audit_receipt",
]
