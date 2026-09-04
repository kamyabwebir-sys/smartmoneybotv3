from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.token_safety_rule_read_model import (
    TokenSafetyRuleReadModel,
    TokenSafetyRuleReadRow,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "token_safety_rule_query.v1"


@dataclass(frozen=True, slots=True)
class TokenSafetyRuleQueryResult:
    rows: tuple[TokenSafetyRuleReadRow, ...]
    query_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple):
            raise TypeError("rows must be a tuple")
        if not isinstance(self.query_id, str) or not self.query_id.strip():
            raise ValueError("query_id must be non-empty")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported rule query schema_version")
        expected = deterministic_id(
            "token_safety_rule_query",
            {
                "evaluation_ids": tuple(
                    row.evaluation.evaluation_id for row in self.rows
                ),
                "schema_version": self.schema_version,
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


def query_token_safety_rules(
    model: TokenSafetyRuleReadModel,
    *,
    observation_id: str | None = None,
    rule_id: str | None = None,
    triggered: bool | None = None,
) -> TokenSafetyRuleQueryResult:
    if not isinstance(model, TokenSafetyRuleReadModel):
        raise TypeError("model must be TokenSafetyRuleReadModel")
    if observation_id is not None and (
        not isinstance(observation_id, str) or not observation_id.strip()
    ):
        raise ValueError("observation_id must be non-empty")
    if rule_id is not None and (not isinstance(rule_id, str) or not rule_id.strip()):
        raise ValueError("rule_id must be non-empty")
    if triggered is not None and not isinstance(triggered, bool):
        raise TypeError("triggered must be boolean")
    rows = tuple(
        row
        for row in model.rows
        if (observation_id is None or row.evaluation.observation_id == observation_id.strip())
        and (rule_id is None or row.evaluation.rule_id == rule_id.strip())
        and (triggered is None or row.evaluation.triggered is triggered)
    )
    return TokenSafetyRuleQueryResult(
        rows=rows,
        query_id=deterministic_id(
            "token_safety_rule_query",
            {
                "evaluation_ids": tuple(
                    row.evaluation.evaluation_id for row in rows
                ),
                "schema_version": _SCHEMA_VERSION,
            },
        ),
    )


__all__ = ["TokenSafetyRuleQueryResult", "query_token_safety_rules"]
