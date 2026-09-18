"""ASGI application factory."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from smart_money.adapters.http.routes.health import router as health_router
from smart_money.adapters.http.routes.v1 import router as v1_router


def create_app() -> FastAPI:
    """Return a fully wired FastAPI ASGI application."""
    app = FastAPI(
        title="Smart Money Dashboard",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    app.include_router(health_router)
    app.include_router(v1_router, prefix="/api/v1")

    @app.exception_handler(HTTPException)
    async def _http_exc_handler(request: Request, exc: HTTPException) -> JSONResponse:
        # detail may be a dict (domain errors) or a plain string (framework errors)
        if isinstance(exc.detail, dict):
            body = exc.detail
        else:
            body = {
                "code": f"http_{exc.status_code}",
                "message": str(exc.detail),
                "details": {},
            }
        return JSONResponse(status_code=exc.status_code, content=body)

    return app


# Module-level ASGI callable for uvicorn / gunicorn
app = create_app()
