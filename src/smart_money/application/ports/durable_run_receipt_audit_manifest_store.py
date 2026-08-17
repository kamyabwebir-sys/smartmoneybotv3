from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, runtime_checkable

from smart_money.application.durable_run_receipt_audit import (
    DurableRunReceiptAuditManifest,
)


@runtime_checkable
class DurableRunReceiptAuditManifestStore(Protocol):
    """Append-only persistence port for durable-run audit manifests."""

    def append(self, manifest: DurableRunReceiptAuditManifest) -> str: ...

    def get(
        self,
        audit_id: str,
    ) -> DurableRunReceiptAuditManifest | None: ...

    def iter_manifests(
        self,
    ) -> Iterator[DurableRunReceiptAuditManifest]: ...

    def contains_content_hash(
        self,
        content_hash: str,
        manifest_count: int,
    ) -> bool: ...

    @property
    def manifest_count(self) -> int: ...

    @property
    def content_hash(self) -> str: ...


__all__ = ["DurableRunReceiptAuditManifestStore"]
