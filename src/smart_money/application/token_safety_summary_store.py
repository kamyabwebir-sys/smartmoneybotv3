from __future__ import annotations
import json
from pathlib import Path
from smart_money.application.token_safety_evidence_summary import TokenSafetyEvidenceSummary

class TokenSafetySummaryStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._items: dict[str, TokenSafetyEvidenceSummary] = {}

    def save(self, summary: TokenSafetyEvidenceSummary) -> str:
        if not isinstance(summary, TokenSafetyEvidenceSummary):
            raise TypeError("summary must be TokenSafetyEvidenceSummary")
        self._items[summary.summary_id] = summary
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"schema_version":"token_safety_summary_store.v1",
            "items":[s.canonical_dict() for s in self._items.values()]},
            sort_keys=True, separators=(",", ":")), encoding="utf-8")
        return summary.summary_id

    def get(self, summary_id: str) -> TokenSafetyEvidenceSummary | None:
        return self._items.get(summary_id)

__all__ = ["TokenSafetySummaryStore"]
