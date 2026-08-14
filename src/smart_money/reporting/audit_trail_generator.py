from __future__ import annotations

from pathlib import Path
from typing import Any

from smart_money.application.analytics import ReplayAnalysisResult
from smart_money.application.score_traceability import ScoreEvidenceContribution
from smart_money.core.serialization import canonicalize

_REPORT_SCHEMA_VERSION = "markdown_audit_trail.v1"
_TABLE_HEADER = (
    "| Evidence ID | Source | Type | Timestamp | Status | Component | Delta |",
    "|---|---|---|---:|---|---|---:|",
)


def _display_value(value: Any) -> str:
    canonical = canonicalize(value)
    if canonical is None:
        return "null"
    if isinstance(canonical, bool):
        return "true" if canonical else "false"
    return str(canonical)


def _escape_cell(value: Any) -> str:
    return (
        _display_value(value)
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r\n", "<br>")
        .replace("\n", "<br>")
        .replace("\r", "<br>")
    )


def _contribution_row(item: ScoreEvidenceContribution) -> str:
    values = (
        item.evidence_id,
        item.source_id,
        item.evidence_type,
        item.timestamp,
        item.status,
        item.score_component,
        item.score_delta,
    )
    return "| " + " | ".join(_escape_cell(value) for value in values) + " |"


def _evidence_table(
    contributions: tuple[ScoreEvidenceContribution, ...],
) -> list[str]:
    rows = [*_TABLE_HEADER]
    if not contributions:
        rows.append("| _none_ | — | — | — | — | — | — |")
        return rows
    rows.extend(_contribution_row(item) for item in contributions)
    return rows


def render_markdown_audit_trail(result: ReplayAnalysisResult) -> str:
    """Render a deterministic, evidence-linked audit report without raw data."""
    if not isinstance(result, ReplayAnalysisResult):
        raise TypeError("result must be a ReplayAnalysisResult")

    trace = result.trace
    scored = tuple(
        item for item in trace.contributions if item.status == "scored"
    )
    non_contributing = tuple(
        item for item in trace.contributions if item.status != "scored"
    )
    lines = [
        "# Replay Analysis Audit Trail",
        "",
        f"- Report schema: `{_REPORT_SCHEMA_VERSION}`",
        f"- Trace ID: `{trace.trace_id}`",
        f"- Replay manifest ID: `{trace.replay_manifest_id}`",
        f"- Integrity ID: `{trace.integrity_id}`",
        f"- Ledger SHA-256: `{trace.ledger_content_hash}`",
        f"- Score output SHA-256: `{trace.score_output_hash}`",
        f"- Score: `{_display_value(result.report.score)}`",
        f"- Evidence count: `{result.report.evidence_count}`",
        "",
        "## Score Breakdown",
        "",
        "| Component | Value |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {_escape_cell(component)} | "
        f"{_escape_cell(result.report.score_breakdown[component])} |"
        for component in sorted(result.report.score_breakdown)
    )
    lines.extend(
        [
            "",
            "## Confirmed Scoring Evidence",
            "",
            *_evidence_table(scored),
            "",
            "## Rejected or Non-Contributing Evidence",
            "",
            *_evidence_table(non_contributing),
            "",
            (
                "_This report is deterministic analytical evidence. "
                "It is not a trading instruction or risk calculation._"
            ),
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown_audit_trail(
    result: ReplayAnalysisResult,
    file_path: str | Path,
) -> Path:
    """Write canonical UTF-8/LF Markdown and return its normalized path."""
    path = Path(file_path)
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(render_markdown_audit_trail(result))
    return path


__all__ = ["render_markdown_audit_trail", "write_markdown_audit_trail"]
