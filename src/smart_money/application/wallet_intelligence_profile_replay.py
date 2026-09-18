from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.wallet_intelligence_profile import (
    WalletIntelligenceProfile,
    project_wallet_intelligence_profiles,
)
from smart_money.application.wallet_intelligence_read_model import (
    build_wallet_intelligence_read_model,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_intelligence_profile_replay.v1"


@dataclass(frozen=True, slots=True)
class WalletIntelligenceProfileReplayReceipt:
    profile_id: str
    evidence_id: str
    matches: bool
    replay_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("profile_id", "evidence_id", "replay_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet intelligence profile replay schema_version")
        if self.replay_id != deterministic_id(
            "wallet_intelligence_profile_replay", self.identity_payload()
        ):
            raise ValueError("replay_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "matches": self.matches,
            "profile_id": self.profile_id,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"replay_id": self.replay_id, **self.identity_payload()}


def replay_verify_wallet_intelligence_profile(
    profile: WalletIntelligenceProfile, ledger: EvidenceLedger
) -> WalletIntelligenceProfileReplayReceipt:
    if not isinstance(profile, WalletIntelligenceProfile):
        raise TypeError("profile must be WalletIntelligenceProfile")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    model = build_wallet_intelligence_read_model(ledger)
    rebuilt = next(
        (item for item in project_wallet_intelligence_profiles(model) if item.wallet == profile.wallet),
        None,
    )
    if rebuilt is None or rebuilt.canonical_dict() != profile.canonical_dict():
        raise ValueError("wallet intelligence profile replay does not match source")
    retained = None
    for payload in ledger.iter_payloads():
        if payload.evidence_type != "wallet_intelligence_profile":
            continue
        data = payload.data.get("wallet_intelligence_profile")
        if hasattr(data, "get") and data.get("profile_id") == profile.profile_id:
            retained = payload
            break
    if retained is None:
        raise ValueError("persisted wallet intelligence profile evidence is missing")
    data = retained.data["wallet_intelligence_profile"]
    if dict(data) != profile.canonical_dict():
        raise ValueError("persisted wallet intelligence profile does not match source")
    evidence_id = retained.get_canonical_id()
    return WalletIntelligenceProfileReplayReceipt(
        profile_id=profile.profile_id,
        evidence_id=evidence_id,
        matches=True,
        replay_id=deterministic_id(
            "wallet_intelligence_profile_replay",
            {
                "evidence_id": evidence_id,
                "matches": True,
                "profile_id": profile.profile_id,
                "schema_version": _SCHEMA_VERSION,
            },
        ),
    )


__all__ = [
    "WalletIntelligenceProfileReplayReceipt",
    "replay_verify_wallet_intelligence_profile",
]
