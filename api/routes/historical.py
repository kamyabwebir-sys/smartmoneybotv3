from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request

from smart_money.api.historical import historical_audit, historical_candidates, historical_overview, historical_replay

router = APIRouter(prefix="/api/v1/historical", tags=["historical"])


def _model(request: Request) -> dict[str, Any]:
    return dict(getattr(request.app.state, "historical_model", {"items": ()}))


def _auth(request: Request, authorization: str | None = Header(default=None)) -> None:
    expected = getattr(request.app.state, "historical_read_token", None)
    token = authorization.removeprefix("Bearer ").strip() if authorization else None
    if expected is not None and token != expected:
        raise HTTPException(status_code=401, detail="read-only authentication failed")


@router.get("/overview")
def overview(request: Request, _: None = Depends(_auth)) -> dict[str, Any]:
    return historical_overview(_model(request))


@router.get("/candidates")
def candidates(request: Request, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500), _: None = Depends(_auth)) -> dict[str, Any]:
    return historical_candidates(_model(request), page=page, page_size=page_size)


@router.get("/audit")
def audit(request: Request, _: None = Depends(_auth)) -> dict[str, Any]:
    return historical_audit(_model(request), {"path": "/api/v1/historical/audit"})


@router.post("/replay")
def replay(request: Request, payload: dict[str, Any], _: None = Depends(_auth)) -> dict[str, Any]:
    return historical_replay(payload.get("expected", {}), payload.get("replayed", {}))
