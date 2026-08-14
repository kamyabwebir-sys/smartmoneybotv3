from __future__ import annotations

from collections.abc import Iterator
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable

from .contracts import EvidencePayload


@runtime_checkable
class EvidenceLedger(Protocol):
    """Provider-neutral append-only evidence ledger contract."""

    def append(self, payload: EvidencePayload) -> str:
        """Store payload idempotently and return its canonical identity."""
        ...

    def contains(self, canonical_id: str) -> bool:
        """Return whether canonical identity is present."""
        ...

    def get(self, canonical_id: str) -> EvidencePayload | None:
        """Return the immutable payload for an identity, if present."""
        ...

    def iter_payloads(self) -> Iterator[EvidencePayload]:
        """Iterate payloads in deterministic insertion order."""
        ...

    @property
    def entry_count(self) -> int:
        """Return the number of unique ledger entries."""
        ...


class EvidenceGroundingLedger:
    """Append-only in-memory ledger keyed by canonical evidence identity."""

    def __init__(self) -> None:
        self._entries: dict[str, Mapping[str, Any]] = {}
        self._payloads: dict[str, EvidencePayload] = {}

    def append(self, payload: EvidencePayload) -> str:
        if not isinstance(payload, EvidencePayload):
            raise TypeError("payload must be an EvidencePayload")
        canonical_id = payload.get_canonical_id()
        return self.record(canonical_id, payload)

    def record(self, canonical_id: str, payload: EvidencePayload) -> str:
        if not isinstance(canonical_id, str) or not canonical_id.strip():
            raise ValueError("canonical_id must be a non-empty string")
        if not isinstance(payload, EvidencePayload):
            raise TypeError("payload must be an EvidencePayload")
        if canonical_id != payload.get_canonical_id():
            raise ValueError("canonical_id does not match payload content")

        if canonical_id not in self._entries:
            self._entries[canonical_id] = MappingProxyType(
                {
                    "canonical_id": canonical_id,
                    **payload.canonical_dict(),
                }
            )
            self._payloads[canonical_id] = payload
        return canonical_id

    def contains(self, canonical_id: str) -> bool:
        return canonical_id in self._entries

    def get(self, canonical_id: str) -> EvidencePayload | None:
        return self._payloads.get(canonical_id)

    def iter_payloads(self) -> Iterator[EvidencePayload]:
        return iter(tuple(self._payloads.values()))

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    def get_all(self) -> list[dict[str, Any]]:
        return [dict(entry) for entry in self._entries.values()]

    def count(self) -> int:
        return self.entry_count


__all__ = ["EvidenceGroundingLedger", "EvidenceLedger"]
