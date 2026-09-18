from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from pathlib import Path

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.funding_cluster_store_audit import FundingClusterStoreAuditReceipt
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "funding_cluster_store_audit_store.v1"


class JsonFundingClusterStoreAuditStore:
    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._receipts: dict[str, FundingClusterStoreAuditReceipt] = {}
        self._load_existing()

    def append(self, receipt: FundingClusterStoreAuditReceipt) -> str:
        if not isinstance(receipt, FundingClusterStoreAuditReceipt):
            raise TypeError("receipt must be FundingClusterStoreAuditReceipt")
        existing = self._receipts.get(receipt.audit_id)
        if existing is not None:
            if existing != receipt:
                raise RuntimeError("funding cluster store audit receipt identity collision")
            return receipt.audit_id
        candidate = dict(self._receipts)
        candidate[receipt.audit_id] = receipt
        self._persist(tuple(candidate.values()))
        self._receipts = candidate
        return receipt.audit_id

    def get(self, audit_id: str) -> FundingClusterStoreAuditReceipt | None:
        return self._receipts.get(audit_id)

    def iter_receipts(self) -> Iterator[FundingClusterStoreAuditReceipt]:
        return iter(tuple(self._receipts.values()))

    @property
    def receipt_count(self) -> int:
        return len(self._receipts)

    def _load_existing(self) -> None:
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        source = self._file_path if self._file_path.is_file() else temporary
        if not source.is_file():
            return
        loaded = self._load_path(source)
        if source == temporary:
            atomic_replace(temporary, self._file_path)
        self._receipts = loaded

    def _load_path(self, path: Path) -> dict[str, FundingClusterStoreAuditReceipt]:
        raw = path.read_text(encoding="utf-8")
        document = json.loads(raw)
        if not isinstance(document, dict) or document.get("schema_version") != _SCHEMA_VERSION:
            raise ValueError("invalid funding cluster store audit store schema")
        records = document.get("receipts")
        if not isinstance(records, list) or document.get("content_hash") != _hash(records):
            raise ValueError("funding cluster store audit store content hash mismatch")
        if canonical_json(document) != raw:
            raise ValueError("funding cluster store audit store is not canonical JSON")
        loaded: dict[str, FundingClusterStoreAuditReceipt] = {}
        for record in records:
            receipt = FundingClusterStoreAuditReceipt(
                audit_id=record["audit_id"],
                cluster_id=record["cluster_id"],
                ledger_receipt_id=record["ledger_receipt_id"],
                replay_id=record["replay_id"],
                store_replay_id=record["store_replay_id"],
                replay_matches=record["replay_matches"],
                schema_version=record["schema_version"],
            )
            if receipt.audit_id in loaded:
                raise ValueError("duplicate funding cluster store audit receipt")
            loaded[receipt.audit_id] = receipt
        return loaded

    def _persist(self, receipts: tuple[FundingClusterStoreAuditReceipt, ...]) -> None:
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


__all__ = ["JsonFundingClusterStoreAuditStore"]
