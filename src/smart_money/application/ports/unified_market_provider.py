from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from smart_money.domain.market_identity import ChainId, MarketId
from smart_money.domain.market_state import MarketStateChange, MarketStateCursor


@runtime_checkable
class UnifiedMarketProvider(Protocol):
    """Port for finalized, canonical onchain market state changes."""

    @property
    def provider_id(self) -> str:
        """Return a stable provider identity, including adapter version."""
        ...

    @property
    def chain_id(self) -> ChainId:
        """Return the single chain served by this provider instance."""
        ...

    def stream_state_changes(
        self,
        market: MarketId,
        cursor: MarketStateCursor | None = None,
    ) -> AsyncIterator[MarketStateChange]:
        """Yield finalized changes in ascending deterministic ordering."""
        ...


__all__ = ["UnifiedMarketProvider"]
