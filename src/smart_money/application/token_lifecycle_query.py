from __future__ import annotations

from dataclasses import dataclass
from smart_money.application.token_lifecycle import TokenLifecycleState
from smart_money.application.token_lifecycle_read_model import TokenLifecycleReadModel, TokenLifecycleReadRow
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class TokenLifecycleQueryResult:
    rows: tuple[TokenLifecycleReadRow, ...]
    query_id: str
    schema_version: str = "token_lifecycle_query.v1"


def query_token_lifecycle(
    model: TokenLifecycleReadModel,
    *,
    token_id: str | None = None,
    state: TokenLifecycleState | None = None,
    min_slot: int | None = None,
) -> TokenLifecycleQueryResult:
    if not isinstance(model, TokenLifecycleReadModel):
        raise TypeError("model must be TokenLifecycleReadModel")
    if token_id is not None and (not isinstance(token_id, str) or not token_id.strip()):
        raise ValueError("token_id must be non-empty")
    if state is not None and not isinstance(state, TokenLifecycleState):
        raise TypeError("state must be TokenLifecycleState")
    if min_slot is not None and (isinstance(min_slot, bool) or not isinstance(min_slot, int) or min_slot < 0):
        raise ValueError("min_slot must be non-negative integer")
    rows = tuple(row for row in model.rows if
        (token_id is None or row.lifecycle.token_id == token_id.strip())
        and (state is None or row.lifecycle.state is state)
        and (min_slot is None or row.lifecycle.observed_slot >= min_slot))
    identity = {"lifecycle_ids": tuple(row.lifecycle.lifecycle_id for row in rows), "schema_version": "token_lifecycle_query.v1"}
    return TokenLifecycleQueryResult(rows, deterministic_id("token_lifecycle_query", identity))


__all__ = ["TokenLifecycleQueryResult", "query_token_lifecycle"]
