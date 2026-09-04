from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_intelligence_read_model import (
    WalletIntelligenceReadModel,
    WalletIntelligenceReadRow,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_intelligence_query.v1"


@dataclass(frozen=True, slots=True)
class WalletIntelligenceQueryResult:
    rows: tuple[WalletIntelligenceReadRow, ...]
    query_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple):
            raise TypeError("rows must be a tuple")
        if not isinstance(self.query_id, str) or not self.query_id.strip():
            raise ValueError("query_id must be non-empty")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet intelligence query schema_version")
        expected = deterministic_id(
            "wallet_intelligence_query",
            {
                "schema_version": self.schema_version,
                "evidence_ids": tuple(row.evidence_id for row in self.rows),
            },
        )
        if self.query_id != expected:
            raise ValueError("query_id does not match result")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "rows": tuple(row.canonical_dict() for row in self.rows),
            "schema_version": self.schema_version,
        }


def query_wallet_intelligence(
    model: WalletIntelligenceReadModel,
    *,
    wallet: str | None = None,
    min_from_slot: int | None = None,
    max_to_slot: int | None = None,
    min_completeness_bps: int | None = None,
) -> WalletIntelligenceQueryResult:
    if not isinstance(model, WalletIntelligenceReadModel):
        raise TypeError("model must be WalletIntelligenceReadModel")
    if wallet is not None and (not isinstance(wallet, str) or not wallet.strip()):
        raise ValueError("wallet must be non-empty")
    for name, value in (
        ("min_from_slot", min_from_slot),
        ("max_to_slot", max_to_slot),
        ("min_completeness_bps", min_completeness_bps),
    ):
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise ValueError(f"{name} must be a non-negative integer")
    if (
        min_completeness_bps is not None
        and min_completeness_bps > 10000
    ):
        raise ValueError("min_completeness_bps must be at most 10000")
    if (
        min_from_slot is not None
        and max_to_slot is not None
        and min_from_slot > max_to_slot
    ):
        raise ValueError("min_from_slot cannot exceed max_to_slot")
    rows = tuple(
        row
        for row in model.rows
        if (wallet is None or row.observation.wallet == wallet.strip())
        and (
            min_from_slot is None
            or row.observation.observed_to_slot >= min_from_slot
        )
        and (
            max_to_slot is None
            or row.observation.observed_from_slot <= max_to_slot
        )
        and (
            min_completeness_bps is None
            or row.observation.data_completeness_bps >= min_completeness_bps
        )
    )
    return WalletIntelligenceQueryResult(
        rows=rows,
        query_id=deterministic_id(
            "wallet_intelligence_query",
            {
                "schema_version": _SCHEMA_VERSION,
                "evidence_ids": tuple(row.evidence_id for row in rows),
            },
        ),
    )


__all__ = ["WalletIntelligenceQueryResult", "query_wallet_intelligence"]
