from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from collections.abc import Iterator
from pathlib import Path

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.dashboard_query_audit_receipt import (
    DashboardQueryAuditReceipt,
)
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "dashboard_query_audit_receipt_store.v1"
_DOCUMENT_KEYS = frozenset({"content_hash", "receipts", "schema_version"})
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class JsonDashboardQueryAuditReceiptStore:
    """Atomic, append-only, byte-stable receipt persistence."""

    __slots__ = ("_file_path", "_receipts")

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._receipts: dict[str, DashboardQueryAuditReceipt] = {}
        self._load_existing()

    def append(self, receipt: DashboardQueryAuditReceipt) -> str:
        if not isinstance(receipt, DashboardQueryAuditReceipt):
            raise TypeError("receipt must be a DashboardQueryAuditReceipt")
        existing = self._receipts.get(receipt.receipt_id)
        if existing is not None:
            if existing != receipt:
                raise RuntimeError("dashboard receipt identity collision")
            return receipt.receipt_id
        candidate = dict(self._receipts)
        candidate[receipt.receipt_id] = receipt
        self._persist(tuple(candidate.values()))
        self._receipts = candidate
        return receipt.receipt_id

    def get(self, receipt_id: str) -> DashboardQueryAuditReceipt | None:
        return self._receipts.get(receipt_id)

    def iter_receipts(self) -> Iterator[DashboardQueryAuditReceipt]:
        return iter(tuple(self._receipts.values()))

    @property
    def receipt_count(self) -> int:
        return len(self._receipts)

    @property
    def content_hash(self) -> str:
        return _hash([receipt.canonical_dict() for receipt in self._receipts.values()])

    def _load_existing(self) -> None:
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        if self._file_path.is_file():
            source = self._file_path
            recovering = False
        elif temporary.is_file():
            source = temporary
            recovering = True
        else:
            return
        loaded = self._load_path(source)
        if recovering:
            atomic_replace(temporary, self._file_path)
        self._receipts = loaded

    def _load_path(self, path: Path) -> dict[str, DashboardQueryAuditReceipt]:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"dashboard receipt store is not valid JSON: {path}") from exc
        if not isinstance(document, dict) or set(document) != _DOCUMENT_KEYS:
            raise ValueError("dashboard receipt store keys do not match schema")
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError("unsupported dashboard receipt store schema_version")
        records = document["receipts"]
        content_hash = document["content_hash"]
        if not isinstance(records, list) or not isinstance(content_hash, str):
            raise ValueError("dashboard receipt store payload is invalid")
        if _SHA256_PATTERN.fullmatch(content_hash) is None:
            raise ValueError("content_hash must be lowercase SHA-256 hex")
        if not hmac.compare_digest(content_hash, _hash(records)):
            raise ValueError("dashboard receipt store content hash mismatch")
        if canonical_json(document) != path.read_text(encoding="utf-8"):
            raise ValueError("dashboard receipt store is not canonical JSON")
        loaded: dict[str, DashboardQueryAuditReceipt] = {}
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("dashboard receipt must be an object")
            try:
                receipt = DashboardQueryAuditReceipt(
                    query_id=record["query_id"],
                    status=record["status"],
                    artifact_id=record["artifact_id"],
                    artifact_kind=record["artifact_kind"],
                    output_hash=record["output_hash"],
                    item_count=record["item_count"],
                    schema_versions=tuple(record["schema_versions"]),
                    error_code=record["error_code"],
                    schema_version=record["schema_version"],
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("invalid dashboard query audit receipt") from exc
            if receipt.receipt_id in loaded:
                raise ValueError("duplicate dashboard receipt identity")
            loaded[receipt.receipt_id] = receipt
        return loaded

    def _persist(self, receipts: tuple[DashboardQueryAuditReceipt, ...]) -> None:
        if self._file_path.parent != Path("."):
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
        records = [receipt.canonical_dict() for receipt in receipts]
        document = {
            "content_hash": _hash(records),
            "receipts": records,
            "schema_version": _SCHEMA_VERSION,
        }
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)


def _hash(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


__all__ = ["JsonDashboardQueryAuditReceiptStore"]
