from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from smart_money.core.ids import deterministic_id
from smart_money.reporting.macro_markdown_report import (
    PersianMacroMarkdownReport,
)


@runtime_checkable
class MacroReportSnapshotLike(Protocol):
    report_id: str
    model_id: str
    explanation_id: str
    subject_id: str
    markdown: str
    content_hash: str


@dataclass(frozen=True, slots=True)
class DashboardMacroReadResponse:
    """Read-only dashboard contract backed by canonical report data."""

    model_id: str
    report_id: str
    explanation_id: str
    subject_id: str
    markdown: str
    snapshot_content_hash: str
    schema_version: str = "dashboard_macro_read_response.v1"

    def __post_init__(self) -> None:
        for field_name in (
            "model_id",
            "report_id",
            "explanation_id",
            "subject_id",
            "markdown",
            "snapshot_content_hash",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if len(self.snapshot_content_hash) != 64 or any(
            character not in "0123456789abcdef"
            for character in self.snapshot_content_hash
        ):
            raise ValueError("snapshot_content_hash must be lowercase SHA-256 hex")
        if self.schema_version != "dashboard_macro_read_response.v1":
            raise ValueError("unsupported dashboard macro response schema_version")

    @classmethod
    def from_report(
        cls,
        report: PersianMacroMarkdownReport,
        snapshot: MacroReportSnapshotLike,
    ) -> DashboardMacroReadResponse:
        if not isinstance(report, PersianMacroMarkdownReport):
            raise TypeError("report must be a PersianMacroMarkdownReport")
        if not isinstance(snapshot, MacroReportSnapshotLike):
            raise TypeError("snapshot must satisfy the macro snapshot contract")
        expected = {
            "model_id": report.model_id,
            "report_id": report.report_id,
            "explanation_id": report.explanation_id,
            "subject_id": report.subject_id,
            "markdown": report.markdown,
        }
        for field_name, value in expected.items():
            if getattr(snapshot, field_name) != value:
                raise ValueError(f"snapshot {field_name} does not match report")
        return cls(
            model_id=report.model_id,
            report_id=report.report_id,
            explanation_id=report.explanation_id,
            subject_id=report.subject_id,
            markdown=report.markdown,
            snapshot_content_hash=snapshot.content_hash,
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "explanation_id": self.explanation_id,
            "markdown": self.markdown,
            "model_id": self.model_id,
            "report_id": self.report_id,
            "schema_version": self.schema_version,
            "snapshot_content_hash": self.snapshot_content_hash,
            "subject_id": self.subject_id,
        }

    @property
    def response_id(self) -> str:
        return deterministic_id(
            "dashboard_macro_read_response",
            self.canonical_dict(),
        )

    @property
    def subject_kind(self) -> str:
        marker = "- نوع موضوع: `"
        for line in self.markdown.splitlines():
            if line.startswith(marker) and line.endswith("`"):
                return line[len(marker) : -1]
        raise ValueError("dashboard report does not declare subject kind")


__all__ = ["DashboardMacroReadResponse", "MacroReportSnapshotLike"]
