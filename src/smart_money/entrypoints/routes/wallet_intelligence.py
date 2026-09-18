"""
GET-only endpoints for WalletIntelligence read model.
schema_version: wallet_intelligence_read_model.v1

Uses {wallet_address:path} converter so EVM-style 0x… addresses
are captured whole even if future address formats contain slashes.
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from smart_money.application.wallet_intelligence_read_model import (
    WalletIntelligenceReadModel,
    WalletIntelligenceReadRow,
)

router = APIRouter(prefix="/wallet-intelligence", tags=["wallet-intelligence"])

# ---------------------------------------------------------------------------
# Dependency protocol — wire this in api.py / deps.py
# ---------------------------------------------------------------------------
def _get_wallet_intelligence_read_model() -> WalletIntelligenceReadModel:  # pragma: no cover
    """
    Replace with the real provider dependency, e.g.:
        from smart_money.entrypoints.deps import get_wallet_intelligence_read_model
    """
    raise NotImplementedError("wallet_intelligence read-model dependency not wired")


WalletIntelligenceReadModelDep = Annotated[
    WalletIntelligenceReadModel,
    Depends(_get_wallet_intelligence_read_model),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _find_rows(
    model: WalletIntelligenceReadModel,
    wallet: str,
) -> list[WalletIntelligenceReadRow]:
    """Return all rows for a wallet address (may span multiple observation windows)."""
    return [r for r in model.rows if r.observation.wallet == wallet]


def _paginate(rows: tuple, limit: int, offset: int) -> tuple:
    return rows[offset : offset + limit]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get(
    "/",
    summary="List wallet intelligence observations (paginated)",
    response_class=JSONResponse,
)
def list_wallet_intelligence(
    model: WalletIntelligenceReadModelDep,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, Any]:
    rows = _paginate(model.rows, limit, offset)
    return {
        "schema_version": model.schema_version,
        "model_id": model.model_id,
        "limit": limit,
        "offset": offset,
        "total": len(model.rows),
        "rows": [row.canonical_dict() for row in rows],
    }


@router.get(
    "/{wallet_address:path}",
    summary="Get all observations for a wallet address",
    response_class=JSONResponse,
)
def get_wallet_intelligence(
    wallet_address: str,
    model: WalletIntelligenceReadModelDep,
) -> dict[str, Any]:
    rows = _find_rows(model, wallet_address)
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"wallet {wallet_address!r} not found",
        )
    # Multiple rows = multiple observation windows for the same wallet — not a 409
    return {
        "schema_version": model.schema_version,
        "model_id": model.model_id,
        "wallet": wallet_address,
        "rows": [r.canonical_dict() for r in rows],
    }
