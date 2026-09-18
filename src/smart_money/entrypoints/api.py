"""ASGI application — smartmoneybotv3 web layer."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Ordered startup and shutdown hooks (expand in W2/W3)."""
    # -- startup --
    yield
    # -- shutdown --


def create_app() -> FastAPI:
    """Construct and return the configured ASGI application."""
    return FastAPI(
        title="Smart Money",
        description=(
            "Deterministic, explainable, replayable market-structure "
            "and discovery platform."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )


app: FastAPI = create_app()