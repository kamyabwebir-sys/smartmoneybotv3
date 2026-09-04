from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.core.ids import deterministic_id
from smart_money.domain.token_safety import TokenSafetyObservation


@dataclass(frozen=True, slots=True)
class TokenSafetyReplayReceipt:
    observation_id: str
    evidence_id: str
    matches: bool
    replay_id: str
    schema_version: str = "token_safety_replay.v1"

    def __post_init__(self) -> None:
        for name in ("observation_id", "evidence_id", "replay_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != "token_safety_replay.v1":
            raise ValueError("unsupported token safety replay schema_version")
        if self.replay_id != deterministic_id(
            "token_safety_replay", self.identity_payload()
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


def replay_verify_token_safety_observation(
    observation: TokenSafetyObservation, ledger: EvidenceLedger
) -> TokenSafetyReplayReceipt:
    if not isinstance(observation, TokenSafetyObservation):
        raise TypeError("observation must be TokenSafetyObservation")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    retained_payload = None
    for payload in ledger.iter_payloads():
        if payload.evidence_type != "token_safety_observation":
            continue
        data = payload.data.get("token_safety")
        if not hasattr(data, "get"):
            raise ValueError("invalid token safety payload in Ledger")
        if data.get("observation_id") == observation.observation_id:
            retained_payload = payload
            break
    if retained_payload is None:
        raise ValueError("persisted token safety evidence is missing")
    data = retained_payload.data["token_safety"]
    if dict(data) != observation.canonical_dict():
        raise ValueError("persisted token safety observation does not match source")
    evidence_id = retained_payload.get_canonical_id()
    return TokenSafetyReplayReceipt(
        observation_id=observation.observation_id,
        evidence_id=evidence_id,
        matches=True,
        replay_id=deterministic_id(
            "token_safety_replay",
            {
                "evidence_id": evidence_id,
                "matches": True,
                "observation_id": observation.observation_id,
                "schema_version": "token_safety_replay.v1",
            },
        ),
    )


__all__ = ["TokenSafetyReplayReceipt", "replay_verify_token_safety_observation"]
