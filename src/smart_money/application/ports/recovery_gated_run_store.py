from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, runtime_checkable

from smart_money.application.recovery_gated_ingestion import (
    RecoveryGatedIngestionResult,
)


@runtime_checkable
class RecoveryGatedRunStore(Protocol):
    """Application port for append-only recovery-gated run receipts."""

    def append(self, result: RecoveryGatedIngestionResult) -> str:
        """Persist a run receipt atomically and return its identity."""
        ...

    def get(self, run_id: str) -> RecoveryGatedIngestionResult | None:
        """Return one persisted run receipt by identity."""
        ...

    def iter_results(self) -> Iterator[RecoveryGatedIngestionResult]:
        """Iterate results in deterministic insertion order."""
        ...

    @property
    def result_count(self) -> int:
        """Return the number of unique persisted run receipts."""
        ...

    @property
    def content_hash(self) -> str:
        """Return the hash of the canonical run receipt collection."""
        ...


__all__ = ["RecoveryGatedRunStore"]
