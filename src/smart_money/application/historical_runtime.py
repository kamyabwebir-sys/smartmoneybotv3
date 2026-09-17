from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class HistoricalJsonStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": "solana_historical_runtime.v1", "items": ()}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return dict(data) if isinstance(data, dict) else {"items": ()}

    def save(self, model: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(model, sort_keys=True, default=list, indent=2), encoding="utf-8")


def load_historical_model(path: str | Path = "artifacts/solana/historical_model.json") -> dict[str, Any]:
    return HistoricalJsonStore(path).load()


__all__ = ["HistoricalJsonStore", "load_historical_model"]
