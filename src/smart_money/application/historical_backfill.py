from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from smart_money.core.ids import deterministic_id


def schedule_historical_batches(start_slot: int, end_slot: int, batch_size: int) -> tuple[tuple[int, int], ...]:
    if start_slot < 0 or end_slot < start_slot or batch_size < 1:
        raise ValueError("invalid batch range")
    return tuple((start, min(start + batch_size - 1, end_slot))
                 for start in range(start_slot, end_slot + 1, batch_size))


class TransactionBackfillStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._items: dict[str, Mapping[str, Any]] = {}

    def save(self, signature: str, transaction: Mapping[str, Any]) -> str:
        if not signature.strip() or not isinstance(transaction, Mapping):
            raise ValueError("invalid transaction")
        self._items[signature.strip()] = dict(transaction)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"schema_version": "transaction_backfill.v1", "items": self._items},
                                        sort_keys=True, separators=(",", ":")), encoding="utf-8")
        return signature.strip()

    def get(self, signature: str) -> Mapping[str, Any] | None:
        return self._items.get(signature)


@dataclass(frozen=True, slots=True)
class BackfillCheckpoint:
    batch_index: int
    last_slot: int
    checkpoint_id: str


def build_backfill_checkpoint(batch_index: int, last_slot: int) -> BackfillCheckpoint:
    identity = {"batch_index": batch_index, "last_slot": last_slot, "schema_version": "backfill_checkpoint.v1"}
    return BackfillCheckpoint(batch_index, last_slot, deterministic_id("backfill_checkpoint", identity))


def verify_backfill_checkpoint(checkpoint: BackfillCheckpoint, restored: BackfillCheckpoint) -> bool:
    return checkpoint == restored


def reconcile_historical_activity(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return dict(left) == dict(right)


@dataclass(frozen=True, slots=True)
class BackfillConflictEvidence:
    subject_id: str
    sources: tuple[str, ...]
    reason: str
    evidence_id: str


def build_backfill_conflict(subject_id: str, sources: tuple[str, ...], reason: str) -> BackfillConflictEvidence:
    identity = {"reason": reason.strip(), "schema_version": "backfill_conflict.v1",
                "sources": sources, "subject_id": subject_id.strip()}
    return BackfillConflictEvidence(subject_id, sources, reason,
                                    deterministic_id("backfill_conflict", identity))


@dataclass(frozen=True, slots=True)
class HistoricalDataset:
    records: tuple[Mapping[str, Any], ...]
    dataset_id: str


def build_historical_dataset(records: tuple[Mapping[str, Any], ...]) -> HistoricalDataset:
    identity = {"records": tuple(dict(item) for item in records), "schema_version": "historical_dataset.v1"}
    return HistoricalDataset(records, deterministic_id("historical_dataset", identity))


def rebuild_historical_candidates(dataset: HistoricalDataset) -> tuple[Mapping[str, Any], ...]:
    return tuple(sorted(dataset.records, key=lambda item: (str(item.get("wallet", "")), str(item.get("token", ""))))
                 )


def verify_backfill_replay(dataset: HistoricalDataset, replayed: HistoricalDataset) -> bool:
    return dataset == replayed


@dataclass(frozen=True, slots=True)
class DatasetQualityReport:
    total_records: int
    complete_records: int
    quality_bps: int
    report_id: str


def build_dataset_quality_report(dataset: HistoricalDataset) -> DatasetQualityReport:
    complete = sum(bool(item.get("wallet")) and bool(item.get("token")) for item in dataset.records)
    quality = complete * 10000 // len(dataset.records) if dataset.records else 0
    identity = {"complete_records": complete, "quality_bps": quality,
                "schema_version": "dataset_quality.v1", "total_records": len(dataset.records)}
    return DatasetQualityReport(len(dataset.records), complete, quality,
                                deterministic_id("dataset_quality", identity))


def verify_backfill_release_gate(required: tuple[str, ...], passed: tuple[str, ...]) -> bool:
    return bool(required) and set(required).issubset(passed)


__all__ = [
    "schedule_historical_batches", "TransactionBackfillStore", "BackfillCheckpoint",
    "build_backfill_checkpoint", "verify_backfill_checkpoint", "reconcile_historical_activity",
    "BackfillConflictEvidence", "build_backfill_conflict", "HistoricalDataset",
    "build_historical_dataset", "rebuild_historical_candidates", "verify_backfill_replay",
    "DatasetQualityReport", "build_dataset_quality_report", "verify_backfill_release_gate",
]
