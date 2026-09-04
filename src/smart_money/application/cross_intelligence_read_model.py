from __future__ import annotations
from dataclasses import dataclass
from smart_money.application.cross_intelligence import WalletTokenCrossSubjectContract

@dataclass(frozen=True, slots=True)
class CrossIntelligenceReadModel:
    rows: tuple[WalletTokenCrossSubjectContract, ...]
    schema_version: str = "cross_intelligence_read_model.v1"

def build_cross_intelligence_read_model(rows: tuple[WalletTokenCrossSubjectContract, ...]) -> CrossIntelligenceReadModel:
    if not isinstance(rows, tuple) or not all(isinstance(x, WalletTokenCrossSubjectContract) for x in rows):
        raise TypeError("rows must be tuple of contracts")
    return CrossIntelligenceReadModel(rows)

def query_cross_intelligence(model: CrossIntelligenceReadModel, *, wallet: str | None = None, token: str | None = None) -> tuple[WalletTokenCrossSubjectContract, ...]:
    if not isinstance(model, CrossIntelligenceReadModel):
        raise TypeError("model must be CrossIntelligenceReadModel")
    return tuple(x for x in model.rows if (wallet is None or x.wallet == wallet.strip()) and (token is None or x.token == token.strip()))

__all__ = ["CrossIntelligenceReadModel", "build_cross_intelligence_read_model", "query_cross_intelligence"]
