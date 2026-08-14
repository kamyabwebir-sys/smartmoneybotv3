from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, runtime_checkable

from smart_money.ingestion.contracts import EvidencePayload


@runtime_checkable
class EvidenceLedger(Protocol):
    """Application port for append-only canonical evidence storage."""

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


__all__ = ["EvidenceLedger"]
