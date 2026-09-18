from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from smart_money.application.dashboard_macro_read_index import DashboardMacroReadIndex

SCHEMA_VERSION = "dashboard_http_response.v1"

router = APIRouter()


# ── dependency ────────────────────────────────────────────────────────────────
# Tests override this via app.dependency_overrides[_get_index] = lambda: mock_index
def _get_index() -> DashboardMacroReadIndex:  # pragma: no cover
    raise NotImplementedError(
        "Bind a real DashboardMacroReadIndex via app.dependency_overrides[_get_index]"
    )


IndexDep = Annotated[DashboardMacroReadIndex, Depends(_get_index)]

_HEADERS = {"schema_version": SCHEMA_VERSION}


# ── helpers ───────────────────────────────────────────────────────────────────
def _run_page(
    index: DashboardMacroReadIndex,
    query: str,
    subject_kind: Optional[str],
    status: Optional[str],
    offset: int,
    page_size: int,
) -> JSONResponse:
    try:
        result = index.page(query, subject_kind, status, offset, page_size)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return JSONResponse(content=result, headers=_HEADERS)


# ── routes ────────────────────────────────────────────────────────────────────
@router.get("/health")
async def health() -> JSONResponse:
    return JSONResponse(content={"status": "ok"}, headers=_HEADERS)


@router.get("/ready")
async def ready(index: IndexDep) -> JSONResponse:
    return JSONResponse(content={"status": "ready"}, headers=_HEADERS)


@router.get("/api/v1/overview")
async def overview(
    index: IndexDep,
    query: str = Query(default=""),
    subject_kind: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    offset: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=200),
) -> JSONResponse:
    return _run_page(index, query, subject_kind, status, offset, page_size)


@router.get("/api/v1/opportunity-graph")
async def opportunity_graph(
    index: IndexDep,
    query: str = Query(default=""),
    subject_kind: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    offset: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=200),
) -> JSONResponse:
    return _run_page(index, query, subject_kind, status, offset, page_size)


@router.get("/api/v1/alerts")
async def alerts(
    index: IndexDep,
    query: str = Query(default=""),
    subject_kind: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    offset: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=200),
) -> JSONResponse:
    return _run_page(index, query, subject_kind, status, offset, page_size)