"""
ASGI application entry-point for the Smart Money dashboard layer.

Routes
------
/ready          liveness / readiness probe (no auth)
/dashboard/*    macro overview + subject detail endpoints
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from api.routes import dashboard as _dashboard_module

app = FastAPI(
    title="Smart Money Dashboard",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
)

# ── readiness probe ──────────────────────────────────────────────────────────
@app.get("/ready", include_in_schema=False, response_class=JSONResponse)
async def readiness() -> JSONResponse:
    """Kubernetes / load-balancer health check."""
    return JSONResponse({"status": "ok"})


# ── dashboard routes ─────────────────────────────────────────────────────────
app.include_router(_dashboard_module.router, prefix="/dashboard")