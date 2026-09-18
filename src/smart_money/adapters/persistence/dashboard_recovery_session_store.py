from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from pathlib import Path

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.dashboard_recovery_query_session import (
    DashboardRecoveryQuerySessionReceipt,
)
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "dashboard_recovery_session_store.v1"


class JsonDashboardRecoverySessionStore:
    """Atomic, append-only persistence for gated dashboard session receipts."""

    __slots__ = ("_file_path", "_receipts")

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._receipts: dict[str, DashboardRecoveryQuerySessionReceipt] = {}
        self._load()

    def append(self, receipt: DashboardRecoveryQuerySessionReceipt) -> str:
        if not isinstance(receipt, DashboardRecoveryQuerySessionReceipt):
            raise TypeError("receipt must be a DashboardRecoveryQuerySessionReceipt")
        existing = self._receipts.get(receipt.session_id)
        if existing is not None:
            if existing != receipt:
                raise RuntimeError("session receipt identity collision")
            return receipt.session_id
        candidate = dict(self._receipts)
        candidate[receipt.session_id] = receipt
        self._persist(tuple(candidate.values()))
        self._receipts = candidate
        return receipt.session_id

    def get(self, session_id: str) -> DashboardRecoveryQuerySessionReceipt | None:
        return self._receipts.get(session_id)

    def iter_receipts(self) -> Iterator[DashboardRecoveryQuerySessionReceipt]:
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
            document = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("session store is not valid JSON") from exc
        if not isinstance(document, dict) or set(document) != {
            "content_hash",
            "receipts",
            "schema_version",
        }:
            raise ValueError("session store keys do not match schema")
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError("unsupported session store schema_version")
        records = document["receipts"]
        if not isinstance(records, list) or _digest(records) != document[
            "content_hash"
        ]:
            raise ValueError("session store content hash mismatch")
        if canonical_json(document) != source.read_text(encoding="utf-8"):
            raise ValueError("session store is not canonical JSON")
        loaded: dict[str, DashboardRecoveryQuerySessionReceipt] = {}
        for record in records:
            try:
                receipt = DashboardRecoveryQuerySessionReceipt(
                    session_status=record["session_status"],
                    recovery_receipt_id=record["recovery_receipt_id"],
                    query_id=record["query_id"],
                    query_receipt_id=record["query_receipt_id"],
                    reason_code=record["reason_code"],
                    schema_version=record["schema_version"],
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("invalid session receipt") from exc
            if receipt.session_id in loaded:
                raise ValueError("duplicate session receipt identity")
            loaded[receipt.session_id] = receipt
        if recovering:
            atomic_replace(temporary, self._file_path)
        self._receipts = loaded

    def _persist(
        self,
        receipts: tuple[DashboardRecoveryQuerySessionReceipt, ...],
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


__all__ = ["JsonDashboardRecoverySessionStore"]
