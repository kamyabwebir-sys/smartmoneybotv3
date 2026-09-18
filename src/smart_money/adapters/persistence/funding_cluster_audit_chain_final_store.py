from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from pathlib import Path

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.funding_cluster_audit_chain_final import (
    FundingClusterAuditChainFinalReceipt,
)
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "funding_cluster_audit_chain_final_store.v1"


class JsonFundingClusterAuditChainFinalStore:
    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._receipts: dict[str, FundingClusterAuditChainFinalReceipt] = {}
        self._load_existing()

    def append(self, receipt: FundingClusterAuditChainFinalReceipt) -> str:
        if not isinstance(receipt, FundingClusterAuditChainFinalReceipt):
            raise TypeError("receipt must be FundingClusterAuditChainFinalReceipt")
        existing = self._receipts.get(receipt.final_id)
        if existing is not None:
            if existing != receipt:
                raise RuntimeError("funding cluster audit final identity collision")
            return receipt.final_id
        candidate = dict(self._receipts)
        candidate[receipt.final_id] = receipt
        self._persist(tuple(candidate.values()))
        self._receipts = candidate
        return receipt.final_id

    def get(self, final_id: str) -> FundingClusterAuditChainFinalReceipt | None:
        return self._receipts.get(final_id)

    def iter_receipts(self) -> Iterator[FundingClusterAuditChainFinalReceipt]:
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

    def _load_path(self, path: Path) -> dict[str, FundingClusterAuditChainFinalReceipt]:
        raw = path.read_text(encoding="utf-8")
        document = json.loads(raw)
        if not isinstance(document, dict) or document.get("schema_version") != _SCHEMA_VERSION:
            raise ValueError("invalid funding cluster audit final store schema")
        records = document.get("receipts")
        if not isinstance(records, list) or document.get("content_hash") != _hash(records):
            raise ValueError("funding cluster audit final store content hash mismatch")
        if canonical_json(document) != raw:
            raise ValueError("funding cluster audit final store is not canonical JSON")
        loaded: dict[str, FundingClusterAuditChainFinalReceipt] = {}
        for record in records:
            receipt = FundingClusterAuditChainFinalReceipt(
                accepted=record["accepted"],
                chain_id=record["chain_id"],
                cluster_id=record["cluster_id"],
                final_id=record["final_id"],
                gate_id=record["gate_id"],
                schema_version=record["schema_version"],
                store_verification_id=record["store_verification_id"],
            )
            if receipt.final_id in loaded:
                raise ValueError("duplicate funding cluster audit final receipt")
            loaded[receipt.final_id] = receipt
        return loaded

    def _persist(self, receipts: tuple[FundingClusterAuditChainFinalReceipt, ...]) -> None:
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


__all__ = ["JsonFundingClusterAuditChainFinalStore"]
