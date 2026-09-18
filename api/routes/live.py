"""Authenticated, read-only live batch inspection and human review endpoints."""

from __future__ import annotations

import csv
import hmac
import io
import json
import time
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import Response

from smart_money.adapters.persistence.live_capture_store import (
    read_live_capture_snapshot,
)
from smart_money.application.dashboard_runtime import (
    AlertReviewRecord,
    DashboardOperationalGate,
)
from smart_money.application.independent_quality_evaluation import (
    evaluate_independent_dataset,
)
from smart_money.core.ids import deterministic_id
from smart_money.reporting.solana_dashboard_persian import (
    build_persian_live_report,
)

router = APIRouter(prefix="/api/v1/live", tags=["live-dashboard"])


def _auth(request: Request, authorization: str | None = Header(default=None)) -> None:
    expected = getattr(request.app.state, "live_read_token", None)
    supplied = authorization.removeprefix("Bearer ").strip() if authorization else None
    if not expected or not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(401, "live dashboard authentication failed")


def _snapshot(request: Request) -> dict[str, Any]:
    try:
        snapshot = read_live_capture_snapshot(request.app.state.live_capture_dir)
    except (AttributeError, OSError, ValueError) as exc:
        raise HTTPException(503, "live capture unavailable or corrupt") from exc
    captured = snapshot["report"].get("ingestion", {}).get("captured_at_epoch")
    if type(captured) is not int:
        raise HTTPException(503, "live capture freshness unavailable")
    now = int(time.time())
    return dict(snapshot, freshness={
        "captured_at_epoch": captured,
        "age_seconds": max(0, now - captured),
        "stale": now - captured > request.app.state.live_stale_after_seconds,
    })


@router.get("/overview", dependencies=[Depends(_auth)])
def overview(request: Request) -> dict[str, Any]:
    snapshot = _snapshot(request)
    report = snapshot["report"]
    return {
        "schema_version": "live_dashboard_overview.v1", "read_only": True,
        "identity": snapshot["identity"], "freshness": snapshot["freshness"],
        "counts": {key: report.get(key, 0) for key in ("signature_count", "transaction_count", "candidate_count")},
        "ingestion": report["ingestion"], "gate": report.get("gate", {"passed": False}),
        "candidates": [_candidate_row(row) for row in report.get("ranking", [])],
        "evidence_counts": {
            "funding_edges": len(report.get("funding_graph_evidence", [])),
            "safety_complete": sum(
                row.get("safety_status") == "EVIDENCE_COMPLETE"
                for row in report.get("ranking", [])
            ),
            "safety_incomplete": sum(
                row.get("safety_status") in {"INCOMPLETE", "UNKNOWN"}
                for row in report.get("ranking", [])
            ),
        },
        "failures": report.get("failures", []),
    }


def _candidate_row(row: dict[str, Any]) -> dict[str, Any]:
    candidate = dict(row)
    candidate["candidate_id"] = row.get("candidate_id") or row.get("evidence_id") or row.get("signature")
    candidate["safety_status"] = row.get("safety_status", "UNKNOWN")
    candidate["funding_status"] = row.get("funding_status", "UNKNOWN")
    return candidate


@router.get("/candidates/{candidate_id}", dependencies=[Depends(_auth)])
def candidate_detail(candidate_id: str, request: Request) -> dict[str, Any]:
    snapshot = _snapshot(request)
    report = snapshot["report"]
    candidate = next((_candidate_row(row) for row in report.get("ranking", []) if _candidate_row(row)["candidate_id"] == candidate_id), None)
    if candidate is None:
        raise HTTPException(404, "candidate not found")
    signatures = set(candidate.get("signatures", ()))
    if isinstance(candidate.get("signature"), str):
        signatures.add(candidate["signature"])
    return {
        "schema_version": "live_candidate_detail.v1", "candidate": candidate,
        "freshness": snapshot["freshness"],
        "route_evidence": [row for row in report.get("route_reports", []) if row.get("signature") in signatures],
        "swap_evidence": [row for row in report.get("swap_legs", []) if row.get("signature") in signatures],
        "purchase_evidence": [row for row in report.get("purchase_evaluations", []) if row.get("signature") in signatures],
        "safety_report": {
            "status": candidate["safety_status"],
            "evidence": candidate.get("safety_evidence"),
            "fail_closed": candidate["safety_status"] != "EVIDENCE_COMPLETE",
        },
        "funding_graph": {
            "status": candidate["funding_status"],
            "edges": candidate.get("funding_evidence", []),
            "edge_ids": candidate.get("funding_edge_ids", []),
            "fail_closed": candidate["funding_status"] != "VERIFIED",
        },
    }


@router.get("/candidates/{candidate_id}/funding", dependencies=[Depends(_auth)])
def candidate_funding(candidate_id: str, request: Request) -> dict[str, Any]:
    detail = candidate_detail(candidate_id, request)
    return {
        "schema_version": "candidate_funding_graph.v1",
        "candidate_id": candidate_id,
        **detail["funding_graph"],
    }


@router.get("/candidates/{candidate_id}/safety", dependencies=[Depends(_auth)])
def candidate_safety(candidate_id: str, request: Request) -> dict[str, Any]:
    detail = candidate_detail(candidate_id, request)
    return {
        "schema_version": "candidate_token_safety_report.v1",
        "candidate_id": candidate_id,
        **detail["safety_report"],
    }


@router.post("/reviews", dependencies=[Depends(_auth)], status_code=201)
def review(payload: dict[str, Any], request: Request) -> dict[str, str]:
    alert_id, reviewer, status = payload.get("candidate_id"), payload.get("reviewer"), payload.get("status")
    if not all(isinstance(value, str) and value.strip() for value in (alert_id, reviewer, status)):
        raise HTTPException(422, "candidate_id, reviewer and status are required")
    try:
        candidates = {_candidate_row(row)["candidate_id"] for row in _snapshot(request)["report"].get("ranking", [])}
        if alert_id.strip() not in candidates:
            raise ValueError("candidate does not exist in latest batch")
        if status.strip() not in {"ACCEPTED", "REJECTED"}:
            raise ValueError("review must be ACCEPTED or REJECTED")
        identity = {"alert_id": alert_id.strip(), "status": status.strip(), "reviewer": reviewer.strip()}
        record = AlertReviewRecord(identity["alert_id"], identity["status"], identity["reviewer"], deterministic_id("dashboard_alert_review", identity))
        request.app.state.live_review_store.save(record)
    except (ValueError, TypeError, OSError) as exc:
        raise HTTPException(422, "invalid review") from exc
    return record.canonical_dict()


@router.get("/quality", dependencies=[Depends(_auth)])
def quality(request: Request) -> dict[str, Any]:
    try:
        document = json.loads(request.app.state.live_quality_dataset.read_text(encoding="utf-8"))
        return evaluate_independent_dataset(document).canonical_dict()
    except (AttributeError, OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise HTTPException(503, "independent quality evaluation unavailable") from exc


@router.get("/observations", dependencies=[Depends(_auth)])
def observations(request: Request, page: int = 1, page_size: int = 50) -> dict[str, Any]:
    if page < 1 or not 1 <= page_size <= 200:
        raise HTTPException(422, "invalid observation pagination")
    rows = _snapshot(request)["report"].get("normalized_observations", [])
    if not isinstance(rows, list):
        raise HTTPException(503, "normalized observations unavailable")
    start = (page - 1) * page_size
    return {
        "schema_version": "normalized_observation_query.v1",
        "items": rows[start : start + page_size],
        "page": page,
        "page_size": page_size,
        "read_only": True,
        "total": len(rows),
    }


@router.get("/reports/fa", dependencies=[Depends(_auth)])
def persian_report(request: Request) -> dict[str, Any]:
    return build_persian_live_report(_snapshot(request)["report"])


# ---------------------------------------------------------------------------
# H14 — Export JSON/CSV
# ---------------------------------------------------------------------------

_EXPORT_TABLES = {
    "candidates": "ranking",
    "observations": "normalized_observations",
    "route_reports": "route_reports",
    "swap_legs": "swap_legs",
    "funding_edges": "funding_graph_evidence",
    "failures": "failures",
}


def _export_rows(report: dict[str, Any], table: str) -> list[dict[str, Any]]:
    key = _EXPORT_TABLES.get(table)
    if key is None:
        raise HTTPException(422, "unknown export table")
    rows = report.get(key, [])
    return [dict(row) for row in rows if isinstance(row, dict)]


def _flatten(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


@router.get("/export/{table}", dependencies=[Depends(_auth)])
def export_table(table: str, request: Request, format: str = "json") -> Response:
    if format not in {"json", "csv"}:
        raise HTTPException(422, "format must be json or csv")
    snapshot = _snapshot(request)
    rows = _export_rows(snapshot["report"], table)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    if format == "json":
        document = {
            "schema_version": "live_dashboard_export.v1",
            "read_only": True,
            "table": table,
            "exported_at": stamp,
            "freshness": snapshot["freshness"],
            "identity": snapshot["identity"],
            "items": rows,
        }
        payload = json.dumps(document, ensure_ascii=False, sort_keys=True, default=list)
        return Response(
            content=payload,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{table}-{stamp}.json"'},
        )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    columns = sorted({key for row in rows for key in row}) if rows else []
    writer.writerow(columns)
    for row in rows:
        writer.writerow([_flatten(row.get(column)) for column in columns])
    return Response(
        content=buffer.getvalue().encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{table}-{stamp}.csv"'},
    )


# ---------------------------------------------------------------------------
# H15 — Dashboard production gate
# ---------------------------------------------------------------------------


@router.get("/gate", dependencies=[Depends(_auth)])
def production_gate(request: Request) -> dict[str, Any]:
    snapshot = _snapshot(request)
    report = snapshot["report"]
    ranking = report.get("ranking", []) if isinstance(report.get("ranking"), list) else []
    candidate_count = report.get("candidate_count", 0)
    checks = {
        "capture_available": True,
        "data_fresh": not snapshot["freshness"]["stale"],
        "has_transactions": report.get("transaction_count", 0) > 0,
        "has_candidates": candidate_count > 0,
        "recovery_ok": bool(report.get("recovery_ok", False)),
        "no_unresolved_failures": not report.get("failures", []),
        "safety_evaluated": bool(ranking) and all(
            row.get("safety_status") in {"EVIDENCE_COMPLETE", "RISK_PRESENT", "INCOMPLETE", "UNKNOWN"}
            for row in ranking
        ),
        "funding_evaluated": bool(ranking) and all(
            row.get("funding_status") in {"VERIFIED", "NOT_OBSERVED", "UNKNOWN"}
            for row in ranking
        ),
        "batch_gate_passed": bool(report.get("gate", {}).get("passed", False)),
    }
    gate = DashboardOperationalGate.evaluate(checks)
    # Human release approval is required on top of operational checks; it is
    # read from the review store so the dashboard can only ever open when a
    # human previously recorded approval for this deployment.
    return {
        "schema_version": "live_dashboard_production_gate.v1",
        "read_only": True,
        "gate_id": gate.gate_id,
        "ready": gate.ready,
        "checks": gate.checks,
        "failed_checks": [key for key, value in gate.checks.items() if not value],
        "freshness": snapshot["freshness"],
        "fail_closed": True,
        "note": "operational readiness only; production release additionally requires the human-gated release receipt",
    }
