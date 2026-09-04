from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.token_safety_candidate_read_model import (
    TokenSafetyCandidateReadModel,
    TokenSafetyCandidateReadRow,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class TokenSafetyCandidateQueryResult:
    rows: tuple[TokenSafetyCandidateReadRow, ...]
    query_id: str
    schema_version: str = "token_safety_candidate_query.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple):
            raise TypeError("rows must be a tuple")
        if not isinstance(self.query_id, str) or not self.query_id.strip():
            raise ValueError("query_id must be non-empty")
        if self.schema_version != "token_safety_candidate_query.v1":
            raise ValueError("unsupported query schema_version")
        expected = deterministic_id(
            "token_safety_candidate_query",
            {"binding_ids": tuple(row.binding.binding_id for row in self.rows), "schema_version": self.schema_version},
        )
        if self.query_id != expected:
            raise ValueError("query_id does not match result")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "rows": tuple(row.canonical_dict() for row in self.rows),
            "schema_version": self.schema_version,
        }


def query_token_safety_candidates(
    model: TokenSafetyCandidateReadModel,
    *,
    wallet: str | None = None,
    token: str | None = None,
    min_liquidity: int | None = None,
    max_concentration_bps: int | None = None,
    require_no_mint_authority: bool = False,
    require_no_freeze_authority: bool = False,
) -> TokenSafetyCandidateQueryResult:
    if not isinstance(model, TokenSafetyCandidateReadModel):
        raise TypeError("model must be TokenSafetyCandidateReadModel")
    if min_liquidity is not None and (
        isinstance(min_liquidity, bool) or not isinstance(min_liquidity, int) or min_liquidity < 0
    ):
        raise ValueError("min_liquidity must be non-negative integer")
    if max_concentration_bps is not None and (
        isinstance(max_concentration_bps, bool)
        or not isinstance(max_concentration_bps, int)
        or not 0 <= max_concentration_bps <= 10000
    ):
        raise ValueError("max_concentration_bps must be between 0 and 10000")
    if not isinstance(require_no_mint_authority, bool) or not isinstance(
        require_no_freeze_authority, bool
    ):
        raise TypeError("authority filters must be boolean")
    rows = []
    for row in model.rows:
        binding = row.binding
        if wallet is not None and binding.wallet != wallet.strip():
            continue
        if token is not None and binding.token != token.strip():
            continue
        if min_liquidity is not None and binding.liquidity_amount < min_liquidity:
            continue
        if (
            max_concentration_bps is not None
            and binding.holder_concentration_bps > max_concentration_bps
        ):
            continue
        if require_no_mint_authority and binding.mint_authority is not None:
            continue
        if require_no_freeze_authority and binding.freeze_authority is not None:
            continue
        rows.append(row)
    rows.sort(key=lambda row: (row.candidate.first_slot, row.binding.wallet, row.binding.token))
    return TokenSafetyCandidateQueryResult(
        rows=tuple(rows),
        query_id=deterministic_id(
            "token_safety_candidate_query",
            {
                "binding_ids": tuple(row.binding.binding_id for row in rows),
                "schema_version": "token_safety_candidate_query.v1",
            },
        ),
    )


__all__ = ["TokenSafetyCandidateQueryResult", "query_token_safety_candidates"]
