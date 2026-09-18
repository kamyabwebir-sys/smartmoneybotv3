from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.funding_graph_read_model import (
    FundingGraphReadModel,
    FundingGraphReadRow,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "funding_edge_query.v1"


@dataclass(frozen=True, slots=True)
class FundingEdgeQueryResult:
    rows: tuple[FundingGraphReadRow, ...]
    query_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple) or not all(
            isinstance(item, FundingGraphReadRow) for item in self.rows
        ):
            raise TypeError("rows must be a tuple of FundingGraphReadRow")
        if not isinstance(self.query_id, str) or not self.query_id.strip():
            raise ValueError("query_id must be non-empty")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported funding edge query schema_version")
        expected = deterministic_id(
            "funding_edge_query",
            {
                "evidence_ids": tuple(item.ledger_evidence_id for item in self.rows),
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


def query_funding_edges(
    model: FundingGraphReadModel,
    *,
    source_wallet: str | None = None,
    target_wallet: str | None = None,
    chain: str | None = None,
    min_native_amount: int | None = None,
    min_observed_slot: int | None = None,
    max_observed_slot: int | None = None,
) -> FundingEdgeQueryResult:
    if not isinstance(model, FundingGraphReadModel):
        raise TypeError("model must be FundingGraphReadModel")
    for name, value in (
        ("source_wallet", source_wallet),
        ("target_wallet", target_wallet),
        ("chain", chain),
    ):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{name} must be non-empty")
    for name, value in (
        ("min_native_amount", min_native_amount),
        ("min_observed_slot", min_observed_slot),
        ("max_observed_slot", max_observed_slot),
    ):
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise ValueError(f"{name} must be a non-negative integer")
    if (
        min_observed_slot is not None
        and max_observed_slot is not None
        and min_observed_slot > max_observed_slot
    ):
        raise ValueError("min_observed_slot cannot exceed max_observed_slot")
    selected = tuple(
        row
        for row in model.rows
        if (source_wallet is None or row.evidence.source_wallet == source_wallet.strip())
        and (target_wallet is None or row.evidence.target_wallet == target_wallet.strip())
        and (chain is None or row.evidence.chain == chain.strip())
        and (
            min_native_amount is None
            or row.evidence.native_amount >= min_native_amount
        )
        and (
            min_observed_slot is None
            or row.evidence.observed_slot >= min_observed_slot
        )
        and (
            max_observed_slot is None
            or row.evidence.observed_slot <= max_observed_slot
        )
    )
    return FundingEdgeQueryResult(
        rows=selected,
        query_id=deterministic_id(
            "funding_edge_query",
            {
                "evidence_ids": tuple(item.ledger_evidence_id for item in selected),
                "schema_version": _SCHEMA_VERSION,
            },
        ),
    )


__all__ = ["FundingEdgeQueryResult", "query_funding_edges"]
