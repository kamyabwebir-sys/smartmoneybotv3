from __future__ import annotations
import json
from pathlib import Path
from smart_money.application.token_lifecycle_query import TokenLifecycleQueryResult

class TokenLifecycleQueryStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._items: dict[str, TokenLifecycleQueryResult] = {}

    def save(self, result: TokenLifecycleQueryResult) -> str:
        if not isinstance(result, TokenLifecycleQueryResult):
            raise TypeError("result must be TokenLifecycleQueryResult")
        self._items[result.query_id] = result
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"schema_version":"token_lifecycle_query_store.v1",
            "items":[{"query_id": r.query_id, "schema_version": r.schema_version,
                      "rows":[row.canonical_dict() for row in r.rows]} for r in self._items.values()]},
            sort_keys=True, separators=(",", ":")), encoding="utf-8")
        return result.query_id

    def get(self, query_id: str) -> TokenLifecycleQueryResult | None:
        return self._items.get(query_id)

__all__ = ["TokenLifecycleQueryStore"]
