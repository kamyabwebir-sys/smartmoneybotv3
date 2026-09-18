from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.durable_ingestion_commit import (
    DurableIngestionCommitReceipt,
)
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "durable_ingestion_commit_store.v1"
_DOCUMENT_KEYS = frozenset({"schema_version", "content_hash", "receipts"})
_RECEIPT_KEYS = frozenset(
    {
        "receipt_id",
        "session_id",
        "provider_id",
        "market_id",
        "event_id",
        "source_event_id",
        "evidence_id",
        "ledger_content_hash",
        "checkpoint_id",
        "accepted_count",
        "schema_version",
    }
)
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class JsonCommitReceiptStore:
    """Single-writer, append-only, atomic JSON commit-receipt collection."""

    __slots__ = ("_file_path", "_receipts")

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._receipts: dict[str, DurableIngestionCommitReceipt] = {}
        self._load_existing()

    def append(self, receipt: DurableIngestionCommitReceipt) -> str:
        if not isinstance(receipt, DurableIngestionCommitReceipt):
            raise TypeError("receipt must be a DurableIngestionCommitReceipt")

        existing = self._receipts.get(receipt.receipt_id)
        if existing is not None:
            if existing != receipt:
                raise RuntimeError("commit receipt identity collision")
            return receipt.receipt_id

        candidate = dict(self._receipts)
        candidate[receipt.receipt_id] = receipt
        self._persist(tuple(candidate.values()))
        self._receipts = candidate
        return receipt.receipt_id

    def get(self, receipt_id: str) -> DurableIngestionCommitReceipt | None:
        return self._receipts.get(receipt_id)

    def iter_receipts(self) -> Iterator[DurableIngestionCommitReceipt]:
        return iter(tuple(self._receipts.values()))

    @property
    def receipt_count(self) -> int:
        return len(self._receipts)

    @property
    def content_hash(self) -> str:
        return self._compute_content_hash(
            self._serialize_receipts(tuple(self._receipts.values()))
        )

    @property
    def file_path(self) -> Path:
        return self._file_path

    def _load_existing(self) -> None:
        temporary_path = self._temporary_path()
        recovering_temporary_file = False
        if self._file_path.is_file():
            source_path = self._file_path
        elif temporary_path.is_file():
            source_path = temporary_path
            recovering_temporary_file = True
        else:
            return

        try:
            loaded = self._load_from_path(source_path)
        except ValueError as exc:
            if recovering_temporary_file:
                raise ValueError(
                    "temporary commit receipt recovery failed: "
                    f"{temporary_path}"
                ) from exc
            raise
        if recovering_temporary_file:
            atomic_replace(temporary_path, self._file_path)
        self._receipts = loaded

    def _load_from_path(
        self,
        path: Path,
    ) -> dict[str, DurableIngestionCommitReceipt]:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"commit receipt store is not valid JSON: {path}"
            ) from exc
        if not isinstance(document, dict):
            raise ValueError("commit receipt store root must be an object")
        if set(document) != _DOCUMENT_KEYS:
            raise ValueError("commit receipt document keys do not match schema")
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError(
                "unsupported commit receipt store schema_version: "
                f"{document['schema_version']}"
            )

        receipts_data = document["receipts"]
        if not isinstance(receipts_data, list):
            raise ValueError("commit receipts must be a list")
        for receipt_data in receipts_data:
            if not isinstance(receipt_data, dict):
                raise ValueError("each commit receipt must be an object")
            if set(receipt_data) != _RECEIPT_KEYS:
                raise ValueError("commit receipt keys do not match schema")

        content_hash = document["content_hash"]
        if (
            not isinstance(content_hash, str)
            or _SHA256_PATTERN.fullmatch(content_hash) is None
        ):
            raise ValueError(
                "content_hash must be a lowercase SHA-256 hex digest"
            )
        expected_hash = self._compute_content_hash(receipts_data)
        if not hmac.compare_digest(content_hash, expected_hash):
            raise ValueError("commit receipt store content hash mismatch")

        loaded: dict[str, DurableIngestionCommitReceipt] = {}
        for receipt_data in receipts_data:
            try:
                receipt = DurableIngestionCommitReceipt(**receipt_data)
            except (TypeError, ValueError) as exc:
                raise ValueError("invalid durable ingestion commit receipt") from exc
            if receipt.receipt_id in loaded:
                raise ValueError(
                    f"duplicate commit receipt identity: {receipt.receipt_id}"
                )
            loaded[receipt.receipt_id] = receipt
        return loaded

    def _persist(
        self,
        receipts: tuple[DurableIngestionCommitReceipt, ...],
    ) -> None:
        if self._file_path.parent != Path("."):
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
        receipts_data = self._serialize_receipts(receipts)
        document = {
            "schema_version": _SCHEMA_VERSION,
            "content_hash": self._compute_content_hash(receipts_data),
            "receipts": receipts_data,
        }
        temporary_path = self._temporary_path()
        with temporary_path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary_path, self._file_path)

    @staticmethod
    def _serialize_receipts(
        receipts: tuple[DurableIngestionCommitReceipt, ...],
    ) -> list[dict[str, str | int]]:
        return [receipt.canonical_dict() for receipt in receipts]

    @staticmethod
    def _compute_content_hash(receipts_data: list[dict[str, Any]]) -> str:
        material = {
            "schema_version": _SCHEMA_VERSION,
            "receipts": receipts_data,
        }
        return hashlib.sha256(
            canonical_json(material).encode("utf-8")
        ).hexdigest()

    def _temporary_path(self) -> Path:
        return self._file_path.with_name(f"{self._file_path.name}.tmp")


__all__ = ["JsonCommitReceiptStore"]
