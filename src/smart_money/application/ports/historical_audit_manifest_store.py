from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, runtime_checkable

from smart_money.application.historical_receipt_audit import (
    HistoricalReceiptAuditManifest,
)


@runtime_checkable
class HistoricalAuditManifestStore(Protocol):
    """Application port for append-only historical audit manifests."""

    def append(self, manifest: HistoricalReceiptAuditManifest) -> str:
        """Persist a manifest atomically and return its deterministic identity."""
        ...

    def get(
        self,
        audit_id: str,
    ) -> HistoricalReceiptAuditManifest | None:
        """Return one historical audit manifest by identity."""
        ...

    def iter_manifests(self) -> Iterator[HistoricalReceiptAuditManifest]:
        """Iterate manifests in deterministic insertion order."""
        ...

    @property
    def manifest_count(self) -> int:
        """Return the number of unique persisted manifests."""
        ...

    @property
    def content_hash(self) -> str:
        """Return the hash of the canonical manifest collection."""
        ...


__all__ = ["HistoricalAuditManifestStore"]
