from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.dashboard_session_audit_head_anchor import (
    DashboardSessionAuditHeadAnchor,
)
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "dashboard_session_audit_head_anchor_store.v1"


class JsonDashboardSessionAuditHeadAnchorStore:
    """Atomic persistence for one trusted session chain head anchor."""

    __slots__ = ("_file_path", "_anchor")

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._anchor: DashboardSessionAuditHeadAnchor | None = None
        self._load()

    def save(self, anchor: DashboardSessionAuditHeadAnchor) -> str:
        if not isinstance(anchor, DashboardSessionAuditHeadAnchor):
            raise TypeError("anchor must be a DashboardSessionAuditHeadAnchor")
        if self._anchor is not None and self._anchor != anchor:
            raise RuntimeError("session audit head rollback or fork rejected")
        document = {
            "anchor": anchor.canonical_dict(),
            "content_hash": _digest(anchor.canonical_dict()),
            "schema_version": _SCHEMA_VERSION,
        }
        if self._file_path.parent != Path("."):
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)
        self._anchor = anchor
        return anchor.anchor_id

    def load(self) -> DashboardSessionAuditHeadAnchor | None:
        return self._anchor

    def _load(self) -> None:
        if not self._file_path.is_file():
            return
        try:
            document = json.loads(self._file_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("session head anchor is not valid JSON") from exc
        if not isinstance(document, dict) or set(document) != {
            "anchor",
            "content_hash",
            "schema_version",
        }:
            raise ValueError("session head anchor keys do not match schema")
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError("unsupported session head anchor store schema_version")
        payload = document["anchor"]
        if not isinstance(payload, dict) or _digest(payload) != document[
            "content_hash"
        ]:
            raise ValueError("session head anchor content hash mismatch")
        if canonical_json(document) != self._file_path.read_text(encoding="utf-8"):
            raise ValueError("session head anchor is not canonical JSON")
        try:
            self._anchor = DashboardSessionAuditHeadAnchor(**payload)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid session head anchor") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


__all__ = ["JsonDashboardSessionAuditHeadAnchorStore"]
