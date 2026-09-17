"""API v1 dashboard routes.

Design constraints (derived from compiled test contracts):
  - GET-only: FastAPI returns 405 automatically for other verbs.
  - limit cap: le=50 causes FastAPI to return 422 for oversized requests.
  - KeyError  -> 404  (unknown subject / response_id)
  - ValueError -> 409  (ambiguous subject_id)
  - All success responses aastAPI to return 422 for oversized requests.
  - KeyError  -> 404  (unknown subject / response_id)
  - ValueError -> 409  (ambiguous subject_id)
  - All success responses are wrapped in dashboard_http_response.v1.
"""
from __future__ import annotations

async def _get_index() -> DashboardMacroReadIndex:  # pragma: no cover
    """
    Placeholder provider.  Replace via app.dependency_overrides in tests
    or register a real factory once the read-model wiring is complete.

    Example (in conftest.py):
        app.dependency_overrides[_get_index] = lambda: my_index_instance
    """
    raise NotImplementedError(
        "DashboardMacroReadIndex provider is not configured; "
        "register a factory via app.dependency_overrides[_get_index]."
    )


IndexDep = Annotated[DashboardMacroReadIndex, Depends(_get_index)]


# ── shared pagination dependency ──────────────────────────────────────────

def _pagination(
    query: str = Query(default=""),
    subject_kind: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=_PAGE_SIZE_CAP, ge=1, le=_PAGE_SIZE_CAP),
) -> dict:
    return {
        "query": query,
        "subject_kind": subject_kind,
        "status": status,
        "offset": offset,
        "limit": limit,
    }


Pagination = Annotated[dict, Depends(_pagination)]


# ── helpers ───────────────────────────────────────────────────────────────

def _ok(data: dict) -> JSONResponse:
    return JSONResponse(
        content={"schema_version": "dashboard_http_response.v1", "data": data}
    )


def _run_page(index: DashboardMacroReadIndex, params: dict) -> JSONResponse:
    try:
        page = index.page(**params)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": str(exc), "details": {}},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": "ambiguous", "message": str(exc), "details": {}},
        ) from exc
    return _ok(page.canonical_dict())


# ── endpoints ─────────────────────────────────────────────────────────────

@router.get("/overview")
async def overview(index: IndexDep, params: Pagination) -> JSONResponse:
    """Paginated macro read-index overview."""
    return _run_page(index, params)


@router.get("/opportunity-graph")
async def opportunity_graph(index: IndexDep, params: Pagination) -> JSONResponse:
    """Paginated opportunity graph slice."""
    return _run_page(index, params)


@router.get("/alerts")
async def alerts(index: IndexDep, params: Pagination) -> JSONResponse:
    """Paginated alerts slice."""
    return _run_page(index, params)
