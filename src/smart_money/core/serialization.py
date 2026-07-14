from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from collections.abc import Mapping, Sequence
from typing import Any

from .time import datetime_to_canonical


def _decimal_to_canonical(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("Decimal values must be finite")
    return format(value.normalize(), "f")


def canonicalize(value: Any) -> Any:
    """Convert supported values into canonical JSON-compatible values."""
    if is_dataclass(value):
        return canonicalize(asdict(value))

    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key in sorted(value.keys()):
            if not isinstance(key, str):
                raise TypeError("canonical dict keys must be strings")
            normalized[key] = canonicalize(value[key])
        return normalized

    if isinstance(value, tuple):
        return [canonicalize(item) for item in value]

    if isinstance(value, list):
        return [canonicalize(item) for item in value]

    if isinstance(value, datetime):
        return datetime_to_canonical(value)

    if isinstance(value, Decimal):
        return _decimal_to_canonical(value)

    if isinstance(value, Enum):
        return canonicalize(value.value)

    if isinstance(value, float):
        raise TypeError("float values are not allowed in canonical identity serialization")

    if value is None or isinstance(value, str | int | bool):
        return value

    raise TypeError(f"unsupported value for canonical serialization: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    """Return deterministic canonical JSON.

    JSON keys are sorted and separators are fixed to make hashing stable.
    """
    return json.dumps(
        canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
