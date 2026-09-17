"""Application factory for the SmartMoney dashboard API."""
from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import dashboard, historical, live, route_evidence
from smart_money.application.dashboard_macro_read_index import DashboardMacroReadIndex
from smart_money.application.dashboard_runtime import JsonAlertReviewStore
from smart_money.application.historical_runtime import load_historical_model


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Production lifespan: wire real infrastructure into app.state.
    In tests this is bypassed via dependency_overrides so no real
    index is needed at startup.
    """
    # Import here to avoid pulling heavy deps in test collection.
    try:
        from smart_money.adapters.evm_v3_provider import (
            build_macro_read_index,
        )
        app.state.macro_read_index = await build_macro_read_index()
    except (ImportError, AttributeError):
        app.state.macro_read_index = DashboardMacroReadIndex.from_responses([])
    app.state.historical_model = load_historical_model()
    app.state.historical_read_token = os.getenv("SMART_MONEY_DASHBOARD_TOKEN")
    app.state.live_read_token = os.getenv("SMART_MONEY_DASHBOARD_TOKEN")
    app.state.live_capture_dir = Path(os.getenv("SMART_MONEY_LIVE_CAPTURE_DIR", "artifacts/solana/live_session.capture"))
    app.state.live_stale_after_seconds = int(os.getenv("SMART_MONEY_LIVE_STALE_SECONDS", "300"))
    app.state.live_review_store = JsonAlertReviewStore(os.getenv("SMART_MONEY_LIVE_REVIEW_STORE", "artifacts/dashboard/live_reviews.json"))
    app.state.live_quality_dataset = Path(os.getenv("SMART_MONEY_QUALITY_DATASET", "fixtures/quality/independent-evaluation-v1.json"))
    yield
    # teardown (if needed) goes here


def create_app(*, lifespan_enabled: bool = True) -> FastAPI:
    """
    Return a fully-wired FastAPI application.

    Parameters
    ----------
    lifespan_enabled:
        Set to False in unit tests that inject their own state via
        dependency_overrides without needing the real lifespan.
    """
    app = FastAPI(
        title="SmartMoney Dashboard API",
        version="0.1.0",
        lifespan=lifespan if lifespan_enabled else None,
    )
    app.include_router(route_evidence.router)
    app.include_router(dashboard.router)
    app.include_router(historical.router)
    app.include_router(live.router)
    app.mount(
        "/dashboard/assets",
        StaticFiles(directory=Path(__file__).resolve().parent / "static"),
        name="dashboard-assets",
    )
    @app.get("/dashboard/historical", include_in_schema=False)
    def historical_dashboard() -> FileResponse:
        return FileResponse("artifacts/dashboard/historical.html")
    @app.get("/dashboard/live", include_in_schema=False)
    def live_dashboard() -> FileResponse:
        return FileResponse(Path(__file__).resolve().parent / "static/live.html")
    return app


# Convenience singleton used by `uvicorn api.main:app`
app = create_app()
