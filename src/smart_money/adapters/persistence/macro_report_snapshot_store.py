from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.reporting.macro_markdown_report import (
    PersianMacroMarkdownReport,
)

_SCHEMA_VERSION = "macro_report_snapshot.v1"
_DOCUMENT_KEYS = frozenset(
    {
        "schema_version",
        "report_id",
        "model_id",
        "explanation_id",
        "subject_id",
        "markdown",
        "content_hash",
    }
)


@dataclass(frozen=True, slots=True)
class MacroReportSnapshot:
    report_id: str
    model_id: str
    explanation_id: str
    subject_id: str
    markdown: str
    content_hash: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "report_id",
            "model_id",
            "explanation_id",
            "subject_id",
            "markdown",
            "content_hash",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if len(self.content_hash) != 64 or any(
            character not in "0123456789abcdef" for character in self.content_hash
        ):
            raise ValueError("content_hash must be lowercase SHA-256 hex")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported macro report snapshot schema_version")
        expected = _content_hash(self.markdown)
        if not hmac.compare_digest(self.content_hash, expected):
            raise ValueError("macro report snapshot content hash mismatch")

    @classmethod
    def from_report(
        cls,
        report: PersianMacroMarkdownReport,
    ) -> MacroReportSnapshot:
        if not isinstance(report, PersianMacroMarkdownReport):
            raise TypeError("report must be a PersianMacroMarkdownReport")
        return cls(
            report_id=report.report_id,
            model_id=report.model_id,
            explanation_id=report.explanation_id,
            subject_id=report.subject_id,
            markdown=report.markdown,
            content_hash=_content_hash(report.markdown),
        )

    def canonical_dict(self) -> dict[str, str]:
        return {
            "content_hash": self.content_hash,
            "explanation_id": self.explanation_id,
            "markdown": self.markdown,
            "model_id": self.model_id,
            "report_id": self.report_id,
            "schema_version": self.schema_version,
            "subject_id": self.subject_id,
        }


@dataclass(frozen=True, slots=True)
class MacroReportReplayReceipt:
    report_id: str
    content_hash: str
    matches: bool
    schema_version: str = "macro_report_replay.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.report_id, str) or not self.report_id.strip():
            raise ValueError("report_id must be a non-empty string")
        if len(self.content_hash) != 64:
            raise ValueError("content_hash must be a SHA-256 hex digest")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be a boolean")
        if self.schema_version != "macro_report_replay.v1":
            raise ValueError("unsupported macro report replay schema_version")


def _content_hash(markdown: str) -> str:
    return hashlib.sha256(markdown.encode("utf-8")).hexdigest()


def _canonical_json(document: dict[str, str]) -> str:
    return json.dumps(
        document,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


class JsonMacroReportSnapshotStore:
    """Atomic, byte-stable persistence for one canonical macro report."""

    def save(
        self,
        report: PersianMacroMarkdownReport,
        file_path: str | os.PathLike[str],
    ) -> MacroReportSnapshot:
        snapshot = MacroReportSnapshot.from_report(report)
        path = Path(file_path)
        if path.parent != Path("."):
            path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f"{path.name}.tmp")
        serialized = _canonical_json(snapshot.canonical_dict())
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, path)
        return snapshot

    def load(
        self,
        file_path: str | os.PathLike[str],
    ) -> MacroReportSnapshot:
        path = Path(file_path)
        try:
            document: Any = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"macro report snapshot is not valid JSON: {path}") from exc
        if not isinstance(document, dict) or set(document) != _DOCUMENT_KEYS:
            raise ValueError("macro report snapshot keys do not match schema")
        snapshot = MacroReportSnapshot(
            report_id=document["report_id"],
            model_id=document["model_id"],
            explanation_id=document["explanation_id"],
            subject_id=document["subject_id"],
            markdown=document["markdown"],
            content_hash=document["content_hash"],
            schema_version=document["schema_version"],
        )
        if _canonical_json(snapshot.canonical_dict()) != path.read_text(
            encoding="utf-8"
        ):
            raise ValueError("macro report snapshot is not canonical JSON")
        return snapshot

    def replay(
        self,
        report: PersianMacroMarkdownReport,
        snapshot: MacroReportSnapshot,
    ) -> MacroReportReplayReceipt:
        if not isinstance(report, PersianMacroMarkdownReport):
            raise TypeError("report must be a PersianMacroMarkdownReport")
        if not isinstance(snapshot, MacroReportSnapshot):
            raise TypeError("snapshot must be a MacroReportSnapshot")
        matches = (
            report.report_id == snapshot.report_id
            and report.model_id == snapshot.model_id
            and report.explanation_id == snapshot.explanation_id
            and report.subject_id == snapshot.subject_id
            and hmac.compare_digest(
                _content_hash(report.markdown),
                snapshot.content_hash,
            )
            and report.markdown == snapshot.markdown
        )
        if not matches:
            raise ValueError("macro report replay does not match snapshot")
        return MacroReportReplayReceipt(
            report_id=report.report_id,
            content_hash=snapshot.content_hash,
            matches=True,
        )


__all__ = [
    "JsonMacroReportSnapshotStore",
    "MacroReportReplayReceipt",
    "MacroReportSnapshot",
]
