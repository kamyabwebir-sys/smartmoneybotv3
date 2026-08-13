from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from enum import Enum
from types import MappingProxyType
from typing import Any

_IMMUTABLE_SCALARS = (str, int, bool, Decimal, datetime, Enum, type(None))


def deep_freeze(value: Any, field_name: str = "value") -> Any:
    """Copy supported canonical values into recursively immutable containers."""
    if isinstance(value, Mapping):
        frozen: dict[str, Any] = {}
        for key in value:
            if not isinstance(key, str):
                raise TypeError(f"{field_name} keys must be strings")
            if key in frozen:
                raise ValueError(f"{field_name} contains duplicate keys")
            frozen[key] = deep_freeze(value[key], f"{field_name}.{key}")
        return MappingProxyType(dict(sorted(frozen.items())))

    if isinstance(value, (list, tuple)):
        return tuple(deep_freeze(item, field_name) for item in value)

    if isinstance(value, float):
        raise TypeError(f"{field_name} must not contain float values")

    if isinstance(value, _IMMUTABLE_SCALARS):
        return value

    raise TypeError(
        f"{field_name} contains unsupported value type: {type(value).__name__}"
    )


def deep_thaw(value: Any) -> Any:
    """Return a detached plain representation of a deeply frozen value."""
    if isinstance(value, Mapping):
        return {key: deep_thaw(value[key]) for key in sorted(value)}
    if isinstance(value, tuple):
        return [deep_thaw(item) for item in value]
    return value
