from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.core.ids import deterministic_id
from smart_money.domain.wallet_intelligence import WalletIntelligenceObservation

_SCHEMA_VERSION = "wallet_intelligence_replay.v1"


@dataclass(frozen=True, slots=True)
class WalletIntelligenceReplayReceipt:
    observation_id: str
    evidence_id: str
    matches: bool
    replay_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("observation_id", "evidence_id", "replay_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet intelligence replay schema_version")
        if self.replay_id != deterministic_id(
            "wallet_intelligence_replay", self.identity_payload()
        ):
            raise ValueError("replay_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "matches": self.matches,
            "observation_id": self.observation_id,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"replay_id": self.replay_id, **self.identity_payload()}


def replay_verify_wallet_intelligence_observation(
    observation: WalletIntelligenceObservation, ledger: EvidenceLedger
) -> WalletIntelligenceReplayReceipt:
    if not isinstance(observation, WalletIntelligenceObservation):
        raise TypeError("observation must be WalletIntelligenceObservation")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    retained = None
    for payload in ledger.iter_payloads():
        if payload.evidence_type != "wallet_intelligence_observation":
            continue
        data = payload.data.get("wallet_intelligence")
        if not hasattr(data, "get"):
            raise ValueError("invalid wallet intelligence payload in Ledger")
        if data.get("observation_id") == observation.observation_id:
            retained = payload
            break
    if retained is None:
        raise ValueError("persisted wallet intelligence evidence is missing")
    data = retained.data["wallet_intelligence"]
    if dict(data) != observation.canonical_dict():
        raise ValueError("persisted wallet intelligence does not match source")
    evidence_id = retained.get_canonical_id()
    return WalletIntelligenceReplayReceipt(
        observation_id=observation.observation_id,
        evidence_id=evidence_id,
        matches=True,
        replay_id=deterministic_id(
            "wallet_intelligence_replay",
            {
                "evidence_id": evidence_id,
                "matches": True,
                "observation_id": observation.observation_id,
                "schema_version": _SCHEMA_VERSION,
            },
        ),
    )


__all__ = [
    "WalletIntelligenceReplayReceipt",
    "replay_verify_wallet_intelligence_observation",
]
