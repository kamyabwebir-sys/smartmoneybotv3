"""
api/routes/funding_clusters.py
GET /api/v1/funding-clusters
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from smart_money.application.funding_cluster_query import query_funding_clusters

from api.deps import FundingModelDep

router = APIRouter(tags=["funding-clusters"])

_VALID_RELATIONSHIP_TYPES: frozenset[str] = frozenset(
    {"DIRECT_FUNDING", "MULTI_HOP_FUNDING"}
)


@router.get("/funding-clusters", response_model=None)
def get_funding_clusters(
    model: FundingModelDep,
    wallet: str | None = Query(
        None,
        description="Keep rows where wallet is present in cluster.wallets.",
    ),
    min_size: int | None = Query(
        None,
        ge=2,
        description="Minimum cluster size (inclusive, must be >= 2).",
    ),
    max_size: int | None = Query(
        None,
        ge=2,
        description="Maximum cluster size (inclusive, must be >= 2).",
    ),
    relationship_type: str | None = Query(
        None,
        description="DIRECT_FUNDING | MULTI_HOP_FUNDING",
    ),
) -> dict[str, Any]:
    """Return funding cluster rows matching the supplied filters.

    ``relationship_type`` is validated here before the domain function runs so
    that an unknown value returns 422 rather than a bare 500.
    """
    if relationship_type is not None and relationship_type not in _VALID_RELATIONSHIP_TYPES:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid relationship_type '{relationship_type}'. "
                f"Allowed: {sorted(_VALID_RELATIONSHIP_TYPES)}"
            ),
        )

    try:
        result = query_funding_clusters(
            model,
            wallet=wallet,
            min_size=min_size,
            max_size=max_size,
            relationship_type=relationship_type,
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return result.canonical_dict()
