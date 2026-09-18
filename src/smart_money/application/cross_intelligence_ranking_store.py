from __future__ import annotations
import json
from pathlib import Path
from smart_money.application.cross_intelligence_ranking_query import CrossIntelligenceRankingQueryResult

class CrossIntelligenceRankingStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._items: dict[str, CrossIntelligenceRankingQueryResult] = {}
    def save(self, result: CrossIntelligenceRankingQueryResult) -> str:
        if not isinstance(result, CrossIntelligenceRankingQueryResult):
            raise TypeError("result must be CrossIntelligenceRankingQueryResult")
        self._items[result.query_id] = result
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"schema_version":"cross_intelligence_ranking_store.v1",
            "items":[{"query_id":x.query_id,"result_count":len(x.rows)} for x in self._items.values()]},
            sort_keys=True,separators=(",",":")),encoding="utf-8")
        return result.query_id
    def get(self, query_id: str) -> CrossIntelligenceRankingQueryResult | None:
        return self._items.get(query_id)

__all__ = ["CrossIntelligenceRankingStore"]
