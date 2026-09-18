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


def build_subject_detail(
    *,
    subject_kind: str,
    subject_id: str,
    report: Mapping[str, Any],
) -> dict[str, Any]:
    """Aggregate one wallet's or one token's full evidence from the batch.

    Aggregates ranking rows, normalized observations, swap legs, route
    reports, purchase evaluations and funding edges that reference the
    subject. A subject with no rows raises ValueError (caller maps to 404).
    """
    if subject_kind not in {"wallet", "token"}:
        raise ValueError("subject_kind must be wallet or token")
    key = "wallet" if subject_kind == "wallet" else "mint"
    needle = subject_id.strip()
    if not needle:
        raise ValueError("subject_id must be non-empty")
    ranking = [row for row in report.get("ranking", []) if isinstance(row, Mapping) and str(row.get(key, "")).strip() == needle]
    observations = [row for row in report.get("normalized_observations", []) if isinstance(row, Mapping) and str(row.get(key, "")).strip() == needle]
    signatures = {
        str(row.get("signature", "")).strip()
        for row in (*ranking, *observations) if row.get("signature")
    }
    buy = sum(str(row.get("direction", "")).upper() == "BUY" for row in observations)
    sell = sum(str(row.get("direction", "")).upper() == "SELL" for row in observations)
    unknown = len(observations) - buy - sell
    safety = sorted({str(row.get("safety_status", "UNKNOWN")) for row in ranking})
    funding = sorted({str(row.get("funding_status", "UNKNOWN")) for row in ranking})
    scores = [int(row["score_bps"]) for row in ranking if isinstance(row.get("score_bps"), int)]
    if not ranking and not observations:
        raise ValueError(f"subject not found: {subject_id}")
    return {
        "schema_version": f"live_{subject_kind}_detail.v1",
        "read_only": True,
        "subject_kind": subject_kind,
        "subject_id": needle,
        "summary": {
            "activity_count": len(observations),
            "buy_count": buy,
            "sell_count": sell,
            "unknown_count": unknown,
            "candidate_rows": len(ranking),
            "max_score_bps": max(scores) if scores else None,
            "safety_statuses": safety,
            "funding_statuses": funding,
        },
        "ranking_rows": ranking,
        "observations": observations,
        "route_evidence": [row for row in report.get("route_reports", []) if isinstance(row, Mapping) and str(row.get("signature", "")) in signatures],
        "swap_evidence": [row for row in report.get("swap_legs", []) if isinstance(row, Mapping) and str(row.get("signature", "")) in signatures],
        "purchase_evidence": [row for row in report.get("purchase_evaluations", []) if isinstance(row, Mapping) and str(row.get("signature", "")) in signatures],
        "funding_edges": [row for row in report.get("funding_graph_evidence", []) if isinstance(row, Mapping) and (
            str(row.get("source_wallet", "")) == needle or str(row.get("target_wallet", "")) == needle
        )] if subject_kind == "wallet" else [],
    }


def build_live_production_gate(
    *,
    capture_available: bool,
    data_fresh: bool,
    report: Mapping[str, Any],
) -> dict[str, Any]:
    """Evaluate the live dashboard production gate, fail-closed.

    ``UNKNOWN`` safety/funding status is treated as a failing check: absent
    evidence never counts as evaluated. The result is operational readiness
    only — a production release still requires the human-gated receipt.
    """
    ranking = report.get("ranking", []) if isinstance(report.get("ranking"), list) else []
    checks = {
        "capture_available": bool(capture_available),
        "data_fresh": bool(data_fresh),
        "has_transactions": report.get("transaction_count", 0) > 0,
        "has_candidates": report.get("candidate_count", 0) > 0,
        "recovery_ok": bool(report.get("recovery_ok", False)),
        "no_unresolved_failures": not report.get("failures", []),
        "safety_evaluated": bool(ranking) and all(
            row.get("safety_status") in {"EVIDENCE_COMPLETE", "RISK_PRESENT", "INCOMPLETE"}
            for row in ranking
        ),
        "funding_evaluated": bool(ranking) and all(
            row.get("funding_status") in {"VERIFIED", "NOT_OBSERVED"}
            for row in ranking
        ),
        "batch_gate_passed": bool(report.get("gate", {}).get("passed", False)),
    }
    gate = DashboardOperationalGate.evaluate(checks)
    return {
        "schema_version": "live_dashboard_production_gate.v1",
        "read_only": True,
        "gate_id": gate.gate_id,
        "ready": gate.ready,
        "checks": gate.checks,
        "failed_checks": [key for key, value in gate.checks.items() if not value],
        "fail_closed": True,
        "note": "operational readiness only; production release additionally requires the human-gated release receipt",
    }


__all__ = ["DashboardCache", "DashboardCacheEntry", "AlertReviewRecord", "JsonAlertReviewStore", "DashboardOperationalGate", "build_live_production_gate", "build_subject_detail"]
