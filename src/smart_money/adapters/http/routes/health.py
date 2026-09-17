"""Liveness and readiness probe endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["infra"])

_READY_BODY = {"status": "ok", "schema_version": "dashboard_http_response.v1"}


@router.get("/health")
async def health() -> JSONResponse:
    """Liveness probe – 200 while the process is alive."""
    return JSONResponse(content=_READY_BODY)


@router.get("/ready")
async def ready() -> JSONResponse:
    """Readiness probe – 200 when ready to serve; never cached."""
    return JSONResponse(
        content=_READY_BODY,
        headers={"cache-control": "no-store"},
    )
