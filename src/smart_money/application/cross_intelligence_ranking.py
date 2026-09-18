from __future__ import annotations
from dataclasses import dataclass
from smart_money.application.cross_intelligence import WalletTokenCrossSubjectContract

@dataclass(frozen=True, slots=True)
class CrossIntelligenceRanked:
    contract: WalletTokenCrossSubjectContract
    rank: int
    score: int

def rank_cross_intelligence(rows: tuple[WalletTokenCrossSubjectContract, ...]) -> tuple[CrossIntelligenceRanked, ...]:
    if not isinstance(rows, tuple):
        raise TypeError("rows must be tuple")
    ordered = sorted(rows, key=lambda x: (x.wallet, x.token, x.cross_id))
    return tuple(CrossIntelligenceRanked(x, i, len(ordered)-i+1) for i, x in enumerate(ordered, 1))

__all__ = ["CrossIntelligenceRanked", "rank_cross_intelligence"]
