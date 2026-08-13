from __future__ import annotations

from typing import Any

from contracts import GroundedEntry
from smart_money.core.serialization import canonicalize


class EvidencePopulator:
    """Project grounded evidence into deterministic domain-shaped mappings."""

    def __init__(self) -> None:
        self._domain_evidences: list[dict[str, Any]] = []

    @property
    def domain_evidences(self) -> tuple[dict[str, Any], ...]:
        return tuple(dict(item) for item in self._domain_evidences)

    def populate(self, entry: GroundedEntry) -> dict[str, Any]:
        if not isinstance(entry, GroundedEntry):
            raise TypeError("entry must be a GroundedEntry")

        domain_shape = {
            "id": entry.canonical_id,
            "type": entry.payload.evidence_type,
            "timestamp": entry.payload.timestamp,
            "raw_data": canonicalize(entry.payload.data),
        }
        self._domain_evidences.append(domain_shape)
        return dict(domain_shape)
