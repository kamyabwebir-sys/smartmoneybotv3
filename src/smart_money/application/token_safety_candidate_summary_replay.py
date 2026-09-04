from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.token_safety_candidate_summary_binding import (
    TokenSafetyCandidateSummaryBinding,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "token_safety_candidate_summary_replay.v1"


@dataclass(frozen=True, slots=True)
class TokenSafetyCandidateSummaryReplayReceipt:
    binding_id: str
    evidence_id: str
    matches: bool
    replay_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("binding_id", "evidence_id", "replay_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported candidate summary replay schema_version")
        if self.replay_id != deterministic_id(
            "token_safety_candidate_summary_replay", self.identity_payload()
        ):
            raise ValueError("replay_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "binding_id": self.binding_id,
            "evidence_id": self.evidence_id,
            "matches": self.matches,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"replay_id": self.replay_id, **self.identity_payload()}


def replay_verify_token_safety_candidate_summary_binding(
    binding: TokenSafetyCandidateSummaryBinding, ledger: EvidenceLedger
) -> TokenSafetyCandidateSummaryReplayReceipt:
    if not isinstance(binding, TokenSafetyCandidateSummaryBinding):
        raise TypeError("binding must be TokenSafetyCandidateSummaryBinding")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    retained = None
    for payload in ledger.iter_payloads():
        if payload.evidence_type != "token_safety_candidate_summary_binding":
            continue
        data = payload.data.get("binding")
        if not hasattr(data, "get"):
            raise ValueError("invalid candidate summary payload in Ledger")
        if data.get("binding_id") == binding.binding_id:
            retained = payload
            break
    if retained is None:
        raise ValueError("persisted candidate safety summary evidence is missing")
    data = retained.data["binding"]
    if data.get("candidate") != binding.candidate.canonical_dict():
        raise ValueError("persisted candidate does not match source")
    if data.get("safety_binding") != binding.binding.canonical_dict():
        raise ValueError("persisted safety binding does not match source")
    if data.get("summary") != binding.summary.canonical_dict():
        raise ValueError("persisted summary does not match source")
    evidence_id = retained.get_canonical_id()
    return TokenSafetyCandidateSummaryReplayReceipt(
        binding_id=binding.binding_id,
        evidence_id=evidence_id,
        matches=True,
        replay_id=deterministic_id(
            "token_safety_candidate_summary_replay",
            {
                "binding_id": binding.binding_id,
                "evidence_id": evidence_id,
                "matches": True,
                "schema_version": _SCHEMA_VERSION,
            },
        ),
    )


__all__ = [
    "TokenSafetyCandidateSummaryReplayReceipt",
    "replay_verify_token_safety_candidate_summary_binding",
]
