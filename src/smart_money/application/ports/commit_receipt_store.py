from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, runtime_checkable

from smart_money.application.durable_ingestion_commit import (
    DurableIngestionCommitReceipt,
)


@runtime_checkable
class CommitReceiptStore(Protocol):
    """Application port for append-only durable ingestion receipts."""

    def append(self, receipt: DurableIngestionCommitReceipt) -> str:
        """Persist a receipt atomically and return its deterministic identity."""
        ...

    def get(self, receipt_id: str) -> DurableIngestionCommitReceipt | None:
        """Return one receipt by identity, if present."""
        ...

    def iter_receipts(self) -> Iterator[DurableIngestionCommitReceipt]:
        """Iterate receipts in deterministic insertion order."""
        ...

    @property
    def receipt_count(self) -> int:
        """Return the number of unique persisted receipts."""
        ...

    @property
    def content_hash(self) -> str:
        """Return the hash of the canonical receipt collection."""
        ...


__all__ = ["CommitReceiptStore"]
