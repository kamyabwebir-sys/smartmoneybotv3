from __future__ import annotations

from typing import Protocol, runtime_checkable

from smart_money.domain.market_state import MarketStateCheckpoint


@runtime_checkable
class MarketStateCheckpointStore(Protocol):
    """Application port for one durable market-state resume checkpoint."""

    def save(self, checkpoint: MarketStateCheckpoint) -> None:
        """Persist the checkpoint atomically."""
        ...

    def load(self) -> MarketStateCheckpoint:
        """Load and validate the persisted checkpoint."""
        ...


__all__ = ["MarketStateCheckpointStore"]
