from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def capture_fixture(response: Mapping[str, Any], path: str | Path) -> Path:
    if not isinstance(response, Mapping) or not response:
        raise ValueError("response must be a non-empty mapping")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(dict(response), sort_keys=True, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    return target


__all__ = ["capture_fixture"]
