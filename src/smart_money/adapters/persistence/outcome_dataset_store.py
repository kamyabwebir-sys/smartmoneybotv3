"""Atomic JSON persistence for outcome datasets and human calibration reviews."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class OutcomeDatasetStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def save(self, document: Mapping[str, Any]) -> None:
        if not isinstance(document, Mapping) or not document.get("schema_version"):
            raise ValueError("versioned canonical document required")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(document, sort_keys=True, separators=(",", ":")), encoding="utf-8"
        )
        temporary.replace(self.path)

    def load(self) -> dict[str, Any]:
        document = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(document, dict) or not document.get("schema_version"):
            raise ValueError("stored outcome document is corrupt")
        return document


__all__ = ["OutcomeDatasetStore"]
