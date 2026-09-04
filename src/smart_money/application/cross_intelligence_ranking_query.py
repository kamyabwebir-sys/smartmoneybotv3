from __future__ import annotations
from dataclasses import dataclass
from smart_money.application.cross_intelligence_ranking import CrossIntelligenceRanked
from smart_money.core.ids import deterministic_id

@dataclass(frozen=True, slots=True)
class CrossIntelligenceRankingQueryResult:
    rows: tuple[CrossIntelligenceRanked, ...]
    query_id: str
    schema_version: str = "cross_intelligence_ranking_query.v1"

def query_cross_intelligence_ranking(rows: tuple[CrossIntelligenceRanked, ...], *,
                                     wallet: str | None = None, token: str | None = None,
                                     max_rank: int | None = None) -> CrossIntelligenceRankingQueryResult:
    if not isinstance(rows, tuple) or not all(isinstance(x, CrossIntelligenceRanked) for x in rows):
        raise TypeError("rows must be tuple of CrossIntelligenceRanked")
    if max_rank is not None and (isinstance(max_rank, bool) or not isinstance(max_rank, int) or max_rank < 1):
        raise ValueError("max_rank must be positive")
    selected = tuple(x for x in rows if
                     (wallet is None or x.contract.wallet == wallet.strip())
                     and (token is None or x.contract.token == token.strip())
                     and (max_rank is None or x.rank <= max_rank))
    identity = {"cross_ids": tuple(x.contract.cross_id for x in selected),
                "schema_version": "cross_intelligence_ranking_query.v1"}
    return CrossIntelligenceRankingQueryResult(selected, deterministic_id("cross_intelligence_ranking_query", identity))

__all__ = ["CrossIntelligenceRankingQueryResult", "query_cross_intelligence_ranking"]
