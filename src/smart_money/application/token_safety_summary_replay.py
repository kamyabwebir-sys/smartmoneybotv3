from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.token_safety_evidence_summary import TokenSafetyEvidenceSummary
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "token_safety_evidence_summary_replay.v1"


@dataclass(frozen=True, slots=True)
class TokenSafetySummaryReplayReceipt:
    summary_id: str
    evidence_id: str
    matches: bool
    replay_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("summary_id", "evidence_id", "replay_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported summary replay schema_version")
        if self.replay_id != deterministic_id(
            "token_safety_evidence_summary_replay", self.identity_payload()
        ):
            raise ValueError("replay_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "matches": self.matches,
            "schema_version": self.schema_version,
            "summary_id": self.summary_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"replay_id": self.replay_id, **self.identity_payload()}


def replay_verify_token_safety_evidence_summary(
    summary: TokenSafetyEvidenceSummary, ledger: EvidenceLedger
) -> TokenSafetySummaryReplayReceipt:
    if not isinstance(summary, TokenSafetyEvidenceSummary):
        raise TypeError("summary must be TokenSafetyEvidenceSummary")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    retained = None
    for payload in ledger.iter_payloads():
        if payload.evidence_type != "token_safety_evidence_summary":
            continue
        data = payload.data.get("summary")
        if not hasattr(data, "get"):
            raise ValueError("invalid token safety summary payload in Ledger")
        if data.get("summary_id") == summary.summary_id:
            retained = payload
            break
    if retained is None:
        raise ValueError("persisted token safety summary evidence is missing")
    data = retained.data["summary"]
    if dict(data) != summary.canonical_dict():
        raise ValueError("persisted token safety summary does not match source")
    evidence_id = retained.get_canonical_id()
    return TokenSafetySummaryReplayReceipt(
        summary_id=summary.summary_id,
        evidence_id=evidence_id,
        matches=True,
        replay_id=deterministic_id(
            "token_safety_evidence_summary_replay",
            {
                "evidence_id": evidence_id,
                "matches": True,
                "schema_version": _SCHEMA_VERSION,
                "summary_id": summary.summary_id,
            },
        ),
    )


__all__ = [
    "TokenSafetySummaryReplayReceipt",
    "replay_verify_token_safety_evidence_summary",
]
