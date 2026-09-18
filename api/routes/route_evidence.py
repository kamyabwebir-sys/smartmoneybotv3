"""Bounded offline evidence inspection, sharing historical read authorization."""
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from api.routes.historical import _auth
from smart_money.adapters.persistence.wallet_route_fixture import (
    replay_purchase_fixture,
    replay_route_fixture,
)

router = APIRouter(tags=["route-evidence"])
ROOT = Path(__file__).resolve().parents[2]


@router.get("/api/v1/route-evidence", dependencies=[Depends(_auth)])
def route_evidence(sample: Literal["cycle", "purchase"] = "cycle") -> dict:
    try:
        if sample == "purchase":
            return replay_purchase_fixture(ROOT / "fixtures/solana/mainnet/s12-trending-buy-candidate.json")
        return replay_route_fixture(ROOT / "fixtures/solana/mainnet/s12-cycle.json")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(503, "route evidence unavailable or replay failed") from exc


@router.get("/dashboard/route-evidence", include_in_schema=False)
def route_dashboard() -> FileResponse:
    return FileResponse(ROOT / "api/static/route-evidence.html")
