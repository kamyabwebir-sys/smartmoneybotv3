"""
GET-only endpoints for FundingCluster read model.
schema_version: funding_cluster_read_model.v1
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from smart_money.application.funding_cluster_read_model import (
    FundingClusterReadModel,
    FundingClusterReadRow,
)

router = APIRouter(prefix="/funding-clusters", tags=["funding-clusters"])

# ---------------------------------------------------------------------------
# Dependency protocol — wire this in api.py / deps.py
# ---------------------------------------------------------------------------
def _get_funding_cluster_read_model() -> FundingClusterReadModel:  # pragma: no cover
    """
    Replace with the real provider dependency, e.g.:
        from smart_money.entrypoints.deps import get_funding_cluster_read_model
    """
    raise NotImplementedError("funding_cluster read-model dependency not wired")


FundingClusterReadModelDep = Annotated[
    FundingClusterReadModel,
    Depends(_get_funding_cluster_read_model),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _find_row(model: FundingClusterReadModel, cluster_id: str) -> FundingClusterReadRow:
    matches = [r for r in model.rows if r.cluster.cluster_id == cluster_id]
    if not matches:
        raise HTTPException(status_code=404, detail=f"cluster {cluster_id!r} not found")
    if len(matches) > 1:
        # deterministic model should never produce this; guard defensively
        raise HTTPException(status_code=409, detail=f"cluster_id {cluster_id!r} is ambiguous")
    return matches[0]


def _paginate(rows: tuple, limit: int, offset: int) -> tuple:
    return rows[offset : offset + limit]


# ---------------------------------------------------------------------------
# Endpoints — GET only; FastAPI returns 405 automatically for other verbs
# ---------------------------------------------------------------------------
@router.get(
    "/",
    summary="List funding clusters (paginated)",
    response_class=JSONResponse,
)
def list_funding_clusters(
    model: FundingClusterReadModelDep,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, Any]:
    page = _paginate(model.rows, limit, offset)
    return {
        "schema_version": model.schema_version,
        "model_id": model.model_id,
        "total": len(model.rows),
        "limit": limit,
        "offset": offset,
        "rows": [r.canonical_dict() for r in page],
    }


@router.get(
    "/{cluster_id}",
    summary="Get a single funding cluster by cluster_id",
    response_class=JSONResponse,
)
def get_funding_cluster(
    cluster_id: str,
    model: FundingClusterReadModelDep,
) -> dict[str, Any]:
    row = _find_row(model, cluster_id)
    return {
        "schema_version": model.schema_version,
        "model_id": model.model_id,
        "row": row.canonical_dict(),
    }
