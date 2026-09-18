from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from pathlib import Path

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.dashboard_session_audit_finalizer import (
    DashboardSessionAuditFinalReceipt,
)
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "dashboard_session_audit_final_store.v1"


class JsonDashboardSessionAuditFinalStore:
    """Atomic, append-only persistence for final session audit receipts."""

    __slots__ = ("_file_path", "_receipts")

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._receipts: dict[str, DashboardSessionAuditFinalReceipt] = {}
        self._load()

    def append(self, receipt: DashboardSessionAuditFinalReceipt) -> str:
        if not isinstance(receipt, DashboardSessionAuditFinalReceipt):
            raise TypeError(
                "receipt must be a DashboardSessionAuditFinalReceipt"
            )
        existing = self._receipts.get(receipt.receipt_id)
        if existing is not None:
            if existing != receipt:
                raise RuntimeError("session audit final identity collision")
            return receipt.receipt_id
        candidate = dict(self._receipts)
        candidate[receipt.receipt_id] = receipt
        self._persist(tuple(candidate.values()))
        self._receipts = candidate
        return receipt.receipt_id

    def get(self, receipt_id: str) -> DashboardSessionAuditFinalReceipt | None:
        return self._receipts.get(receipt_id)

    def iter_receipts(self) -> Iterator[DashboardSessionAuditFinalReceipt]:
        return iter(tuple(self._receipts.values()))

    @property
    def receipt_count(self) -> int:
        return len(self._receipts)

    @property
    def content_hash(self) -> str:
        return _digest([item.canonical_dict() for item in self._receipts.values()])

    def _load(self) -> None:
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        if self._file_path.is_file():
            source, recovering = self._file_path, False
        elif temporary.is_file():
            source, recovering = temporary, True
        else:
            return
        try:
            raw = source.read_text(encoding="utf-8")
            document = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("session audit final store is not valid JSON") from exc
        if not isinstance(document, dict) or set(document) != {
            "content_hash",
            "receipts",
            "schema_version",
        }:
            raise ValueError("session audit final store keys do not match schema")
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError("unsupported session audit final store schema_version")
        records = document["receipts"]
        if not isinstance(records, list) or _digest(records) != document[
            "content_hash"
        ]:
            raise ValueError("session audit final store content hash mismatch")
        if canonical_json(document) != raw:
            raise ValueError("session audit final store is not canonical JSON")
        loaded: dict[str, DashboardSessionAuditFinalReceipt] = {}
        for record in records:
            try:
                receipt = DashboardSessionAuditFinalReceipt(**record)
            except (TypeError, ValueError) as exc:
                raise ValueError("invalid session audit final receipt") from exc
            if receipt.receipt_id in loaded:
                raise ValueError("duplicate session audit final receipt ID")
            loaded[receipt.receipt_id] = receipt
        if recovering:
            atomic_replace(temporary, self._file_path)
        self._receipts = loaded

    def _persist(
        self,
        receipts: tuple[DashboardSessionAuditFinalReceipt, ...],
    ) -> None:
        if self._file_path.parent != Path("."):
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
        records = [item.canonical_dict() for item in receipts]
        document = {
            "content_hash": _digest(records),
            "receipts": records,
            "schema_version": _SCHEMA_VERSION,
        }
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)


def _digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


__all__ = ["JsonDashboardSessionAuditFinalStore"]
