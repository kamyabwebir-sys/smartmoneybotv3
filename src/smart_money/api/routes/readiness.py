"""Readiness / liveness probe endpoint."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["ops"])


@router.get("/readiness", summary="Readiness probe", status_code=200)
async def readiness() -> JSONResponse:
    """Return 200 when the application is ready to serve traffic."""
    return JSONResponse(content={"status": "ok"})


__all__ = ["router"]
