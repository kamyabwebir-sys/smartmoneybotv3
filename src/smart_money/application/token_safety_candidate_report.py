from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.token_safety_candidate_read_model import (
    TokenSafetyCandidateReadRow,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class TokenSafetyCandidateEvidenceReport:
    row: TokenSafetyCandidateReadRow
    report_id: str
    schema_version: str = "token_safety_candidate_evidence_report.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.row, TokenSafetyCandidateReadRow):
            raise TypeError("row must be TokenSafetyCandidateReadRow")
        if not isinstance(self.report_id, str) or not self.report_id.strip():
            raise ValueError("report_id must be non-empty")
        if self.schema_version != "token_safety_candidate_evidence_report.v1":
            raise ValueError("unsupported report schema_version")
        expected = deterministic_id(
            "token_safety_candidate_evidence_report",
            {
                "row": self.row.canonical_dict(),
                "schema_version": self.schema_version,
            },
        )
        if self.report_id != expected:
            raise ValueError("report_id does not match report content")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "row": self.row.canonical_dict(),
            "schema_version": self.schema_version,
        }


def build_token_safety_candidate_evidence_report(
    row: TokenSafetyCandidateReadRow,
) -> TokenSafetyCandidateEvidenceReport:
    if not isinstance(row, TokenSafetyCandidateReadRow):
        raise TypeError("row must be TokenSafetyCandidateReadRow")
    return TokenSafetyCandidateEvidenceReport(
        row=row,
        report_id=deterministic_id(
            "token_safety_candidate_evidence_report",
            {
                "row": row.canonical_dict(),
                "schema_version": "token_safety_candidate_evidence_report.v1",
            },
        ),
    )


__all__ = [
    "TokenSafetyCandidateEvidenceReport",
    "build_token_safety_candidate_evidence_report",
]
