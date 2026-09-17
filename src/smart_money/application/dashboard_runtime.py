from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class DashboardCacheEntry:
    key: str
    source_hash: str
    value: Mapping[str, Any]


class DashboardCache:
    def __init__(self) -> None:
        self._entries: dict[str, DashboardCacheEntry] = {}
        self.hits = 0
        self.misses = 0

    def get(self, key: str, source_hash: str) -> Mapping[str, Any] | None:
        entry = self._entries.get(key)
        if entry is None or entry.source_hash != source_hash:
            self.misses += 1
            return None
        self.hits += 1
        return dict(entry.value)

    def put(self, key: str, source_hash: str, value: Mapping[str, Any]) -> None:
        self._entries[key] = DashboardCacheEntry(key, source_hash, dict(value))


@dataclass(frozen=True, slots=True)
class AlertReviewRecord:
    alert_id: str
    status: str
    reviewer: str
    review_id: str

    def __post_init__(self) -> None:
        if self.status not in {"PROPOSED", "ACCEPTED", "REJECTED"}:
            raise ValueError("unsupported alert status")
        expected = deterministic_id("dashboard_alert_review", {"alert_id": self.alert_id, "status": self.status, "reviewer": self.reviewer})
        if self.review_id != expected:
            raise ValueError("review_id mismatch")

    def canonical_dict(self) -> dict[str, str]:
        return {"alert_id": self.alert_id, "reviewer": self.reviewer, "review_id": self.review_id, "status": self.status}


class JsonAlertReviewStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._records: dict[str, AlertReviewRecord] = {}
        if self.path.is_file():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for item in data.get("items", []):
                record = AlertReviewRecord(**item)
                self._records[record.review_id] = record

    def save(self, record: AlertReviewRecord) -> str:
        self._records[record.review_id] = record
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"schema_version": "dashboard_alert_review_store.v1", "items": [item.canonical_dict() for item in sorted(self._records.values(), key=lambda x: x.review_id)]}
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        temporary.replace(self.path)
        return record.review_id

    def get(self, review_id: str) -> AlertReviewRecord | None:
        return self._records.get(review_id)


@dataclass(frozen=True, slots=True)
class DashboardOperationalGate:
    checks: Mapping[str, bool]
    gate_id: str

    @property
    def ready(self) -> bool:
        return bool(self.checks) and all(self.checks.values())

    @classmethod
    def evaluate(cls, checks: Mapping[str, bool]) -> "DashboardOperationalGate":
        normalized = {str(key): bool(value) for key, value in sorted(checks.items())}
        return cls(normalized, deterministic_id("dashboard_operational_gate", {"checks": normalized}))


__all__ = ["DashboardCache", "DashboardCacheEntry", "AlertReviewRecord", "JsonAlertReviewStore", "DashboardOperationalGate"]
