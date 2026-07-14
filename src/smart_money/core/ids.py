from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from .serialization import canonical_json


def deterministic_id(namespace: str, payload: Mapping[str, Any]) -> str:
    """Build a deterministic ID from namespace and canonical payload."""
    if not isinstance(namespace, str) or not namespace.strip():
        raise ValueError("namespace must be a non-empty string")

    if not isinstance(payload, Mapping):
        raise TypeError("payload must be a mapping")

    encoded = canonical_json(payload).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()[:32]
    return f"{namespace.strip()}_{digest}"
