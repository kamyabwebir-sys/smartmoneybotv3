from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from collections.abc import Iterator
from pathlib import Path

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.dashboard_query_replay_verifier import (
    DashboardQueryReplayReceipt,
)
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "dashboard_query_replay_store.v1"
_DOCUMENT_KEYS = frozenset({"content_hash", "receipts", "schema_version"})
_SHA256 = re.compile(r"[0-9a-f]{64}")


class JsonDashboardQueryReplayStore:
    """Atomic, byte-stable persistence for dashboard replay receipts."""

    __slots__ = ("_file_path", "_receipts")

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._receipts: dict[str, DashboardQueryReplayReceipt] = {}
        self._load()

    def append(self, receipt: DashboardQueryReplayReceipt) -> str:
        if not isinstance(receipt, DashboardQueryReplayReceipt):
            raise TypeError("receipt must be a DashboardQueryReplayReceipt")
        existing = self._receipts.get(receipt.verification_id)
        if existing is not None:
            if existing != receipt:
                raise RuntimeError("replay receipt identity collision")
            return receipt.verification_id
        candidate = dict(self._receipts)
        candidate[receipt.verification_id] = receipt
        self._persist(tuple(candidate.values()))
        self._receipts = candidate
        return receipt.verification_id

    def get(self, verification_id: str) -> DashboardQueryReplayReceipt | None:
        return self._receipts.get(verification_id)

    def iter_receipts(self) -> Iterator[DashboardQueryReplayReceipt]:
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
        loaded = self._load_path(source)
        if recovering:
            atomic_replace(temporary, self._file_path)
        self._receipts = loaded

    def _load_path(self, path: Path) -> dict[str, DashboardQueryReplayReceipt]:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"dashboard replay store is not valid JSON: {path}") from exc
        if not isinstance(document, dict) or set(document) != _DOCUMENT_KEYS:
            raise ValueError("dashboard replay store keys do not match schema")
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError("unsupported dashboard replay store schema_version")
        records, content_hash = document["receipts"], document["content_hash"]
        if not isinstance(records, list) or not isinstance(content_hash, str):
            raise ValueError("dashboard replay store payload is invalid")
        if _SHA256.fullmatch(content_hash) is None or not hmac.compare_digest(
            content_hash, _digest(records)
        ):
            raise ValueError("dashboard replay store content hash mismatch")
        if canonical_json(document) != path.read_text(encoding="utf-8"):
            raise ValueError("dashboard replay store is not canonical JSON")
        loaded: dict[str, DashboardQueryReplayReceipt] = {}
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("dashboard replay receipt must be an object")
            try:
                receipt = DashboardQueryReplayReceipt(
                    query_id=record["query_id"],
                    expected_receipt_id=record["expected_receipt_id"],
                    actual_receipt_id=record["actual_receipt_id"],
                    matches=record["matches"],
                    mismatches=tuple(record["mismatches"]),
                    schema_version=record["schema_version"],
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("invalid dashboard replay receipt") from exc
            if receipt.verification_id in loaded:
                raise ValueError("duplicate dashboard replay receipt identity")
            loaded[receipt.verification_id] = receipt
        return loaded

    def _persist(self, receipts: tuple[DashboardQueryReplayReceipt, ...]) -> None:
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


__all__ = ["JsonDashboardQueryReplayStore"]
