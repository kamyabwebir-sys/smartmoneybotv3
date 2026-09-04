from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from pathlib import Path

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.funding_cluster_replay import FundingClusterReplayReceipt
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "funding_cluster_replay_store.v1"


class JsonFundingClusterReplayStore:
    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._receipts: dict[str, FundingClusterReplayReceipt] = {}
        self._load_existing()

    def append(self, receipt: FundingClusterReplayReceipt) -> str:
        if not isinstance(receipt, FundingClusterReplayReceipt):
            raise TypeError("receipt must be FundingClusterReplayReceipt")
        existing = self._receipts.get(receipt.replay_id)
        if existing is not None:
            if existing != receipt:
                raise RuntimeError("funding cluster replay receipt identity collision")
            return receipt.replay_id
        candidate = dict(self._receipts)
        candidate[receipt.replay_id] = receipt
        self._persist(tuple(candidate.values()))
        self._receipts = candidate
        return receipt.replay_id

    def get(self, replay_id: str) -> FundingClusterReplayReceipt | None:
        return self._receipts.get(replay_id)

    def iter_receipts(self) -> Iterator[FundingClusterReplayReceipt]:
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

    def _load_path(self, path: Path) -> dict[str, FundingClusterReplayReceipt]:
        raw = path.read_text(encoding="utf-8")
        document = json.loads(raw)
        if not isinstance(document, dict) or document.get("schema_version") != _SCHEMA_VERSION:
            raise ValueError("invalid funding cluster replay store schema")
        records = document.get("receipts")
        if not isinstance(records, list) or document.get("content_hash") != _hash(records):
            raise ValueError("funding cluster replay store content hash mismatch")
        if canonical_json(document) != raw:
            raise ValueError("funding cluster replay store is not canonical JSON")
        loaded: dict[str, FundingClusterReplayReceipt] = {}
        for record in records:
            receipt = FundingClusterReplayReceipt(
                cluster_id=record["cluster_id"],
                matches=record["matches"],
                replay_id=record["replay_id"],
                schema_version=record["schema_version"],
            )
            if receipt.replay_id in loaded:
                raise ValueError("duplicate funding cluster replay receipt")
            loaded[receipt.replay_id] = receipt
        return loaded

    def _persist(self, receipts: tuple[FundingClusterReplayReceipt, ...]) -> None:
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


__all__ = ["JsonFundingClusterReplayStore"]
