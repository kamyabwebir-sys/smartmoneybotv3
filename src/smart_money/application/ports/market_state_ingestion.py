from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from smart_money.domain.market_identity import ChainId, MarketId
from smart_money.domain.market_state import (
    MarketStateChange,
    MarketStateCheckpoint,
    MarketStateCursor,
)


@runtime_checkable
class IdempotentMarketStateConsumer(Protocol):
    """Accept canonical observations idempotently and acknowledge their ID."""

    async def accept(self, change: MarketStateChange) -> str:
        """Return the accepted change.event_id after durable acceptance."""
        ...


@runtime_checkable
class CheckpointableMarketProvider(Protocol):
    """Provider capabilities required by checkpointed ingestion."""

    @property
    def provider_id(self) -> str:
        ...

    @property
    def chain_id(self) -> ChainId:
        ...

    def stream_state_changes(
        self,
        market: MarketId,
        cursor: MarketStateCursor | None = None,
    ) -> AsyncIterator[MarketStateChange]:
        ...

    def checkpoint_for(
        self,
        change: MarketStateChange,
    ) -> MarketStateCheckpoint:
        ...

    def stream_from_checkpoint(
        self,
        checkpoint: MarketStateCheckpoint,
    ) -> AsyncIterator[MarketStateChange]:
        ...


__all__ = [
    "CheckpointableMarketProvider",
    "IdempotentMarketStateConsumer",
]
