from __future__ import annotations
from dataclasses import dataclass
from smart_money.application.token_outcome_read_model import TokenOutcomeWindowReadModel
from smart_money.application.token_lifecycle_outcome_window import TokenLifecycleOutcomeWindow
from smart_money.core.ids import deterministic_id

@dataclass(frozen=True, slots=True)
class TokenOutcomeQueryResult:
    rows: tuple[TokenLifecycleOutcomeWindow, ...]
    query_id: str
    schema_version: str = "token_outcome_query.v1"

def query_token_outcome_windows(
    model: TokenOutcomeWindowReadModel,
    *,
    token_id: str | None = None,
    min_close_slot: int | None = None,
) -> TokenOutcomeQueryResult:
    if not isinstance(model, TokenOutcomeWindowReadModel):
        raise TypeError("model must be TokenOutcomeWindowReadModel")
    if token_id is not None and (not isinstance(token_id, str) or not token_id.strip()):
        raise ValueError("token_id must be non-empty")
    if min_close_slot is not None and (isinstance(min_close_slot, bool) or not isinstance(min_close_slot, int) or min_close_slot < 0):
        raise ValueError("min_close_slot must be non-negative")
    rows = tuple(row for row in model.rows if
                 (token_id is None or row.lifecycle.token_id == token_id.strip())
                 and (min_close_slot is None or row.close_slot >= min_close_slot))
    identity = {"lifecycle_ids": tuple(row.lifecycle.lifecycle_id for row in rows),
                "schema_version": "token_outcome_query.v1"}
    return TokenOutcomeQueryResult(rows, deterministic_id("token_outcome_query", identity))

__all__ = ["TokenOutcomeQueryResult", "query_token_outcome_windows"]
