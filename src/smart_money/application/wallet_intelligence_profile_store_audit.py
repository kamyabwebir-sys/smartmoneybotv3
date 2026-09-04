from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_intelligence_profile_store_replay import (
    WalletIntelligenceProfileStoreReplayReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_intelligence_profile_store_audit.v1"


@dataclass(frozen=True, slots=True)
class WalletIntelligenceProfileStoreAuditReceipt:
    profile_id: str
    save_id: str
    load_id: str
    replay_id: str
    replay_matches: bool
    audit_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("profile_id", "save_id", "load_id", "replay_id", "audit_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.replay_matches, bool):
            raise TypeError("replay_matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet intelligence profile store audit schema_version")
        if self.audit_id != deterministic_id(
            "wallet_intelligence_profile_store_audit", self.identity_payload()
        ):
            raise ValueError("audit_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "load_id": self.load_id,
            "profile_id": self.profile_id,
            "replay_id": self.replay_id,
            "replay_matches": self.replay_matches,
            "save_id": self.save_id,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"audit_id": self.audit_id, **self.identity_payload()}


def build_wallet_intelligence_profile_store_audit(
    *,
    profile_id: str,
    save_id: str,
    load_id: str,
    replay_receipt: WalletIntelligenceProfileStoreReplayReceipt,
) -> WalletIntelligenceProfileStoreAuditReceipt:
    for name, value in (("profile_id", profile_id), ("save_id", save_id), ("load_id", load_id)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be non-empty")
    if not isinstance(replay_receipt, WalletIntelligenceProfileStoreReplayReceipt):
        raise TypeError("replay_receipt must be WalletIntelligenceProfileStoreReplayReceipt")
    if replay_receipt.profile_id != profile_id.strip():
        raise ValueError("replay receipt profile_id does not match audit profile_id")
    identity = {
        "load_id": load_id.strip(),
        "profile_id": profile_id.strip(),
        "replay_id": replay_receipt.replay_id,
        "replay_matches": replay_receipt.matches,
        "save_id": save_id.strip(),
        "schema_version": _SCHEMA_VERSION,
    }
    return WalletIntelligenceProfileStoreAuditReceipt(
        profile_id=profile_id.strip(),
        save_id=save_id.strip(),
        load_id=load_id.strip(),
        replay_id=replay_receipt.replay_id,
        replay_matches=replay_receipt.matches,
        audit_id=deterministic_id("wallet_intelligence_profile_store_audit", identity),
    )


__all__ = [
    "WalletIntelligenceProfileStoreAuditReceipt",
    "build_wallet_intelligence_profile_store_audit",
]
