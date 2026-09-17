"""
Dashboard subject-detail route.

GET /dashboard/{subject_kind}/{subject_id}

Normalization contract
----------------------
* subject_kind  →  .upper()
* status        →  normalised inside DashboardSubjectDetailQuery

Error mapping (fail-closed)
---------------------------
KeyError   → HTTP 404  (SUBJECT_NOT_FOUND)
ValueError → HTTP 409  (QUERY_CONFLICT)
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from smart_money.application.dashboard_query_endpoint import DashboardQueryEndpoint
from smart_money.application.dashboard_subject_detail_query import (
    DashboardSubjectDetailQuery,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _endpoint_dependency() -> DashboardQueryEndpoint:  # pragma: no cover
    raise NotImplementedError(
        "DashboardQueryEndpoint dependency has not been wired up. "
        "Call app.dependency_overrides[_endpoint_dependency] = <factory> "
        "before serving requests."
    )


@router.get(
    "/{subject_kind}/{subject_id}",
    summary="Retrieve dashboard detail for a subject",
    response_description="Macro read snapshot for the requested subject",
    status_code=200,
)
async def get_subject_detail(
    subject_kind: str,
    subject_id: str,
    endpoint: Annotated[DashboardQueryEndpoint, Depends(_endpoint_dependency)],
    page: Annotated[int, Query(ge=1, description="1-based page number")] = 1,
    page_size: Annotated[
        int, Query(ge=1, le=200, description="Records per page (max 200)")
    ] = 50,
) -> JSONResponse:
    """
    Dispatch a DashboardSubjectDetailQuery through the application endpoint
    and return the canonical dict of the DashboardMacroReadResponse.
    """
    query = DashboardSubjectDetailQuery(
        subject_kind=subject_kind.upper(),
        subject_id=subject_id,
        page=page,
        page_size=page_size,
    )

    try:
        response = endpoint.execute_with_receipt(query)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail={"error": "SUBJECT_NOT_FOUND", "message": str(exc)},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail={"error": "QUERY_CONFLICT", "message": str(exc)},
        ) from exc

    return JSONResponse(content=response.canonical_dict(), status_code=200)
