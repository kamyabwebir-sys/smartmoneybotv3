from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from smart_money.adapters.persistence.json_ledger import GroundedEntry
from smart_money.core.frozen import deep_freeze
from smart_money.core.serialization import canonicalize


class EvidencePopulator:
    """Project grounded evidence into deeply immutable deterministic mappings."""

    def __init__(self) -> None:
        self._domain_evidences: list[Mapping[str, Any]] = []

    @property
    def domain_evidences(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(self._domain_evidences)

    def populate(self, entry: GroundedEntry) -> Mapping[str, Any]:
        if not isinstance(entry, GroundedEntry):
            raise TypeError("entry must be a GroundedEntry")

        domain_shape = deep_freeze(
            {
                "id": entry.canonical_id,
                "type": entry.payload.evidence_type,
                "timestamp": entry.payload.timestamp,
                "raw_data": canonicalize(entry.payload.data),
            },
            "domain_evidence",
        )
        self._domain_evidences.append(domain_shape)
        return domain_shape


__all__ = ["EvidencePopulator"]
