from __future__ import annotations
from dataclasses import dataclass
from smart_money.application.cross_intelligence_ranking_query import CrossIntelligenceRankingQueryResult
from smart_money.core.ids import deterministic_id

@dataclass(frozen=True, slots=True)
class CrossIntelligenceRankingAuditReceipt:
    query_id: str
    result_count: int
    audit_id: str
    schema_version: str = "cross_intelligence_ranking_audit.v1"

def audit_cross_intelligence_ranking(result: CrossIntelligenceRankingQueryResult) -> CrossIntelligenceRankingAuditReceipt:
    if not isinstance(result, CrossIntelligenceRankingQueryResult):
        raise TypeError("result must be CrossIntelligenceRankingQueryResult")
    identity = {"query_id": result.query_id, "result_count": len(result.rows),
                "schema_version": "cross_intelligence_ranking_audit.v1"}
    return CrossIntelligenceRankingAuditReceipt(result.query_id, len(result.rows),
        deterministic_id("cross_intelligence_ranking_audit", identity))

__all__ = ["CrossIntelligenceRankingAuditReceipt", "audit_cross_intelligence_ranking"]
