from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.token_safety_summary_read_model import (
    TokenSafetySummaryReadModel,
    TokenSafetySummaryReadRow,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "token_safety_summary_query.v1"


@dataclass(frozen=True, slots=True)
class TokenSafetySummaryQueryResult:
    rows: tuple[TokenSafetySummaryReadRow, ...]
    query_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple):
            raise TypeError("rows must be a tuple")
        if not isinstance(self.query_id, str) or not self.query_id.strip():
            raise ValueError("query_id must be non-empty")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported summary query schema_version")
        expected = deterministic_id(
            "token_safety_summary_query",
            {
                "schema_version": self.schema_version,
                "summary_ids": tuple(row.summary.summary_id for row in self.rows),
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


def query_token_safety_summaries(
    model: TokenSafetySummaryReadModel,
    *,
    observation_id: str | None = None,
    min_triggered_rules: int | None = None,
    max_triggered_rules: int | None = None,
    required_rule_ids: tuple[str, ...] = (),
) -> TokenSafetySummaryQueryResult:
    if not isinstance(model, TokenSafetySummaryReadModel):
        raise TypeError("model must be TokenSafetySummaryReadModel")
    if observation_id is not None and (
        not isinstance(observation_id, str) or not observation_id.strip()
    ):
        raise ValueError("observation_id must be non-empty")
    for name, value in (
        ("min_triggered_rules", min_triggered_rules),
        ("max_triggered_rules", max_triggered_rules),
    ):
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise ValueError(f"{name} must be a non-negative integer")
    if (
        min_triggered_rules is not None
        and max_triggered_rules is not None
        and min_triggered_rules > max_triggered_rules
    ):
        raise ValueError("min_triggered_rules cannot exceed max_triggered_rules")
    if not isinstance(required_rule_ids, tuple) or not all(
        isinstance(item, str) and item.strip() for item in required_rule_ids
    ):
        raise TypeError("required_rule_ids must be a tuple of non-empty strings")
    required = frozenset(item.strip() for item in required_rule_ids)
    rows = tuple(
        row
        for row in model.rows
        if (observation_id is None or row.summary.observation_id == observation_id.strip())
        and (
            min_triggered_rules is None
            or row.summary.triggered_rules >= min_triggered_rules
        )
        and (
            max_triggered_rules is None
            or row.summary.triggered_rules <= max_triggered_rules
        )
        and required.issubset(set(row.summary.triggered_rule_ids))
    )
    return TokenSafetySummaryQueryResult(
        rows=rows,
        query_id=deterministic_id(
            "token_safety_summary_query",
            {
                "schema_version": _SCHEMA_VERSION,
                "summary_ids": tuple(row.summary.summary_id for row in rows),
            },
        ),
    )


__all__ = ["TokenSafetySummaryQueryResult", "query_token_safety_summaries"]
