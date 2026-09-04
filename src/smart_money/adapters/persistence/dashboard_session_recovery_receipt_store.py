from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.dashboard_session_recovery_gate import (
    DashboardSessionRecoveryReceipt,
)
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "dashboard_session_recovery_receipt_store.v1"


class JsonDashboardSessionRecoveryReceiptStore:
    """Atomic persistence for the latest session-chain recovery receipt."""

    __slots__ = ("_file_path", "_receipt")

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._receipt: DashboardSessionRecoveryReceipt | None = None
        self._load()

    def save(self, receipt: DashboardSessionRecoveryReceipt) -> str:
        if not isinstance(receipt, DashboardSessionRecoveryReceipt):
            raise TypeError("receipt must be a DashboardSessionRecoveryReceipt")
        if self._receipt is not None and self._receipt != receipt:
            raise RuntimeError("session recovery rollback or overwrite rejected")
        document = {
            "content_hash": _digest(receipt.canonical_dict()),
            "receipt": receipt.canonical_dict(),
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
        self._receipt = receipt
        return receipt.receipt_id

    def load(self) -> DashboardSessionRecoveryReceipt | None:
        return self._receipt

    def _load(self) -> None:
        if not self._file_path.is_file():
            return
        try:
            document = json.loads(self._file_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("session recovery receipt is not valid JSON") from exc
        if not isinstance(document, dict) or set(document) != {
            "content_hash",
            "receipt",
            "schema_version",
        }:
            raise ValueError("session recovery receipt keys do not match schema")
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError("unsupported session recovery store schema_version")
        payload = document["receipt"]
        if not isinstance(payload, dict) or _digest(payload) != document[
            "content_hash"
        ]:
            raise ValueError("session recovery receipt content hash mismatch")
        if canonical_json(document) != self._file_path.read_text(encoding="utf-8"):
            raise ValueError("session recovery receipt is not canonical JSON")
        try:
            self._receipt = DashboardSessionRecoveryReceipt(**payload)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid session recovery receipt") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


__all__ = ["JsonDashboardSessionRecoveryReceiptStore"]
