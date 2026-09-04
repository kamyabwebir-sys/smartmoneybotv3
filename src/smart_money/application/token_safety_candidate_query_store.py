from __future__ import annotations
import json
from pathlib import Path
from smart_money.application.token_safety_candidate_query import TokenSafetyCandidateQueryResult

class TokenSafetyCandidateQueryStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._items: dict[str, TokenSafetyCandidateQueryResult] = {}

    def save(self, result: TokenSafetyCandidateQueryResult) -> str:
        if not isinstance(result, TokenSafetyCandidateQueryResult):
            raise TypeError("result must be TokenSafetyCandidateQueryResult")
        self._items[result.query_id] = result
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"schema_version":"token_safety_candidate_query_store.v1",
            "items":[{"query_id": item.query_id, "schema_version": item.schema_version,
                      "row_count": len(item.rows)} for item in self._items.values()]},
            sort_keys=True, separators=(",", ":")), encoding="utf-8")
        return result.query_id

    def get(self, query_id: str) -> TokenSafetyCandidateQueryResult | None:
        return self._items.get(query_id)

__all__ = ["TokenSafetyCandidateQueryStore"]
