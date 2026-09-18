from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.funding_cluster_read_model import (
    FundingClusterReadModel,
    FundingClusterReadRow,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "funding_cluster_query.v1"


@dataclass(frozen=True, slots=True)
class FundingClusterQueryResult:
    rows: tuple[FundingClusterReadRow, ...]
    query_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple) or not all(
            isinstance(item, FundingClusterReadRow) for item in self.rows
        ):
            raise TypeError("rows must be a tuple of FundingClusterReadRow")
        if not isinstance(self.query_id, str) or not self.query_id.strip():
            raise ValueError("query_id must be non-empty")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported funding cluster query schema_version")
        expected = deterministic_id(
            "funding_cluster_query",
            {
                "cluster_ids": tuple(item.cluster.cluster_id for item in self.rows),
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


def query_funding_clusters(
    model: FundingClusterReadModel,
    *,
    wallet: str | None = None,
    min_size: int | None = None,
    max_size: int | None = None,
    relationship_type: str | None = None,
) -> FundingClusterQueryResult:
    if not isinstance(model, FundingClusterReadModel):
        raise TypeError("model must be FundingClusterReadModel")
    if wallet is not None and (not isinstance(wallet, str) or not wallet.strip()):
        raise ValueError("wallet must be non-empty")
    if relationship_type is not None and relationship_type not in {
        "DIRECT_FUNDING",
        "MULTI_HOP_FUNDING",
    }:
        raise ValueError("unsupported relationship_type")
    for name, value in (("min_size", min_size), ("max_size", max_size)):
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 2
        ):
            raise ValueError(f"{name} must be at least 2")
    if min_size is not None and max_size is not None and min_size > max_size:
        raise ValueError("min_size cannot exceed max_size")
    selected = tuple(
        row
        for row in model.rows
        if (wallet is None or wallet.strip() in row.cluster.wallets)
        and (min_size is None or len(row.cluster.wallets) >= min_size)
        and (max_size is None or len(row.cluster.wallets) <= max_size)
        and (
            relationship_type is None
            or any(
                item.relationship_type == relationship_type
                for item in row.relationships
            )
        )
    )
    return FundingClusterQueryResult(
        rows=selected,
        query_id=deterministic_id(
            "funding_cluster_query",
            {
                "cluster_ids": tuple(item.cluster.cluster_id for item in selected),
                "schema_version": _SCHEMA_VERSION,
            },
        ),
    )


__all__ = ["FundingClusterQueryResult", "query_funding_clusters"]
