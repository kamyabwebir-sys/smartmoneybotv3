"""Authenticated, read-only live batch inspection and human review endpoints."""

from __future__ import annotations

import hmac
import json
import time
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from smart_money.adapters.persistence.live_capture_store import (
    read_live_capture_snapshot,
)
from smart_money.application.dashboard_runtime import (
    AlertReviewRecord,
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
