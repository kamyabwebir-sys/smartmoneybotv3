from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.token_safety_candidate_read_model import (
    build_token_safety_candidate_read_model,
)
from smart_money.application.token_safety_candidate_report import (
    TokenSafetyCandidateEvidenceReport,
    build_token_safety_candidate_evidence_report,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "token_safety_candidate_evidence_report_replay.v1"


@dataclass(frozen=True, slots=True)
class TokenSafetyCandidateReportReplayReceipt:
    report_id: str
    replay_id: str
    matches: bool
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("report_id", "replay_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported report replay schema_version")
        if self.replay_id != deterministic_id(
            "token_safety_candidate_evidence_report_replay",
            self.identity_payload(),
        ):
            raise ValueError("replay_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "matches": self.matches,
            "report_id": self.report_id,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"replay_id": self.replay_id, **self.identity_payload()}


def replay_verify_token_safety_candidate_report(
    ledger: EvidenceLedger,
    expected: TokenSafetyCandidateEvidenceReport,
) -> TokenSafetyCandidateReportReplayReceipt:
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    if not isinstance(expected, TokenSafetyCandidateEvidenceReport):
        raise TypeError("expected must be TokenSafetyCandidateEvidenceReport")
    model = build_token_safety_candidate_read_model(ledger)
    for row in model.rows:
        actual = build_token_safety_candidate_evidence_report(row)
        if actual.report_id != expected.report_id:
            continue
        if actual.canonical_dict() != expected.canonical_dict():
            raise ValueError("replayed report does not match expected report")
        return TokenSafetyCandidateReportReplayReceipt(
            report_id=actual.report_id,
            replay_id=deterministic_id(
                "token_safety_candidate_evidence_report_replay",
                {
                    "matches": True,
                    "report_id": actual.report_id,
                    "schema_version": _SCHEMA_VERSION,
                },
            ),
            matches=True,
        )
    raise ValueError("expected token safety candidate report is missing")


__all__ = [
    "TokenSafetyCandidateReportReplayReceipt",
    "replay_verify_token_safety_candidate_report",
]
