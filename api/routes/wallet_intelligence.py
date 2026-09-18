"""
api/routes/wallet_intelligence.py
GET /api/v1/wallet-intelligence
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from smart_money.application.wallet_intelligence_query import query_wallet_intelligence

from api.deps import WalletModelDep

router = APIRouter(tags=["wallet-intelligence"])


@router.get("/wallet-intelligence", response_model=None)
def get_wallet_intelligence(
    model: WalletModelDep,
    wallet: str | None = Query(
        None,
        description="Filter rows by wallet address (exact match on observation.wallet).",
    ),
    min_from_slot: int | None = Query(
        None,
        ge=0,
        description="Keep rows where observed_from_slot >= this value.",
    ),
    max_to_slot: int | None = Query(
        None,
        ge=0,
        description="Keep rows where observed_to_slot <= this value.",
    ),
    min_completeness_bps: int | None = Query(
        None,
        ge=0,
        le=10_000,
        description="Keep rows where data_completeness_bps >= this value (0–10000).",
    ),
) -> dict[str, Any]:
    """Return wallet intelligence rows matching the supplied filters.

    All parameters are optional; omitting them returns the full model.
    Validation errors (mismatched slot range, empty wallet string, etc.)
    are surfaced as HTTP 422.
    """
    try:
        result = query_wallet_intelligence(
            model,
            wallet=wallet,
            min_from_slot=min_from_slot,
            max_to_slot=max_to_slot,
            min_completeness_bps=min_completeness_bps,
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return result.canonical_dict()
