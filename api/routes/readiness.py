"""Readiness / liveness probe endpoint."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["ops"])


@router.get("/ready", response_model=None, include_in_schema=False)
def readiness_probe() -> dict[str, str]:
    """Return 200 when the service is ready to accept traffic."""
    return {"status": "ok"}


@router.get("/live", response_model=None, include_in_schema=False)
def liveness_probe() -> dict[str, str]:
    """Return 200 as long as the process is alive."""
    return {"status": "ok"}