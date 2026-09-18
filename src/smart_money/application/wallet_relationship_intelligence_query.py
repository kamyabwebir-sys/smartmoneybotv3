from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_relationship_intelligence_read_model import (
    WalletRelationshipIntelligenceReadModel,
    WalletRelationshipIntelligenceReadRow,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_relationship_intelligence_query.v1"


@dataclass(frozen=True, slots=True)
class WalletRelationshipIntelligenceQueryResult:
    rows: tuple[WalletRelationshipIntelligenceReadRow, ...]
    query_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple) or not all(
            isinstance(item, WalletRelationshipIntelligenceReadRow) for item in self.rows
        ):
            raise TypeError("rows must be tuple of WalletRelationshipIntelligenceReadRow")
        if not isinstance(self.query_id, str) or not self.query_id.strip():
            raise ValueError("query_id must be non-empty")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet relationship intelligence query schema_version")
        expected = deterministic_id(
            "wallet_relationship_intelligence_query",
            {
                "intelligence_ids": tuple(
                    item.intelligence.intelligence_id for item in self.rows
                ),
                "schema_version": self.schema_version,
            },
        )
        if self.query_id != expected:
            raise ValueError("query_id does not match result")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "rows": tuple(item.canonical_dict() for item in self.rows),
            "schema_version": self.schema_version,
        }


def query_wallet_relationship_intelligence(
    model: WalletRelationshipIntelligenceReadModel,
    *,
    wallet: str | None = None,
    cluster_id: str | None = None,
    min_relationship_count: int | None = None,
) -> WalletRelationshipIntelligenceQueryResult:
    if not isinstance(model, WalletRelationshipIntelligenceReadModel):
        raise TypeError("model must be WalletRelationshipIntelligenceReadModel")
    for name, value in (("wallet", wallet), ("cluster_id", cluster_id)):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{name} must be non-empty")
    if min_relationship_count is not None and (
        isinstance(min_relationship_count, bool)
        or not isinstance(min_relationship_count, int)
        or min_relationship_count < 0
    ):
        raise ValueError("min_relationship_count must be a non-negative integer")
    selected = tuple(
        row
        for row in model.rows
        if (wallet is None or wallet.strip() in row.intelligence.wallets)
        and (
            cluster_id is None
            or row.intelligence.cluster_id == cluster_id.strip()
        )
        and (
            min_relationship_count is None
            or row.intelligence.relationship_count >= min_relationship_count
        )
    )
    return WalletRelationshipIntelligenceQueryResult(
        rows=selected,
        query_id=deterministic_id(
            "wallet_relationship_intelligence_query",
            {
                "intelligence_ids": tuple(
                    item.intelligence.intelligence_id for item in selected
                ),
                "schema_version": _SCHEMA_VERSION,
            },
        ),
    )


__all__ = [
    "WalletRelationshipIntelligenceQueryResult",
    "query_wallet_relationship_intelligence",
]
