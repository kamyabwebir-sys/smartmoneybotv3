from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.adapters.persistence.wallet_intelligence_profile_store import (
    JsonWalletIntelligenceProfileStore,
)
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.wallet_intelligence_profile import (
    project_wallet_intelligence_profiles,
)
from smart_money.application.wallet_intelligence_read_model import (
    build_wallet_intelligence_read_model,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_intelligence_profile_store_replay.v1"


@dataclass(frozen=True, slots=True)
class WalletIntelligenceProfileStoreReplayReceipt:
    profile_id: str
    matches: bool
    replay_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("profile_id", "replay_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported profile store replay schema_version")
        if self.replay_id != deterministic_id(
            "wallet_intelligence_profile_store_replay", self.identity_payload()
        ):
            raise ValueError("replay_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "matches": self.matches,
            "profile_id": self.profile_id,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"replay_id": self.replay_id, **self.identity_payload()}


def replay_verify_wallet_intelligence_profile_store(
    store: JsonWalletIntelligenceProfileStore,
    ledger: EvidenceLedger,
) -> WalletIntelligenceProfileStoreReplayReceipt:
    if not isinstance(store, JsonWalletIntelligenceProfileStore):
        raise TypeError("store must be JsonWalletIntelligenceProfileStore")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    stored = store.load()
    if stored is None:
        raise ValueError("stored wallet intelligence profile is missing")
    rebuilt = next(
        (
            profile
            for profile in project_wallet_intelligence_profiles(
                build_wallet_intelligence_read_model(ledger)
            )
            if profile.wallet == stored.wallet
        ),
        None,
    )
    if rebuilt is None or rebuilt.canonical_dict() != stored.canonical_dict():
        raise ValueError("stored wallet intelligence profile does not match Ledger replay")
    return WalletIntelligenceProfileStoreReplayReceipt(
        profile_id=stored.profile_id,
        matches=True,
        replay_id=deterministic_id(
            "wallet_intelligence_profile_store_replay",
            {
                "matches": True,
                "profile_id": stored.profile_id,
                "schema_version": _SCHEMA_VERSION,
            },
        ),
    )


__all__ = [
    "WalletIntelligenceProfileStoreReplayReceipt",
    "replay_verify_wallet_intelligence_profile_store",
]
