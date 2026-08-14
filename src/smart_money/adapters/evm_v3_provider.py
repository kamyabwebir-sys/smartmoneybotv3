from __future__ import annotations

from collections.abc import AsyncIterable, AsyncIterator, Callable
from dataclasses import dataclass
from typing import TypeAlias

from smart_money.adapters.evm_v3_shadow import (
    DecodedEvmV3PoolEvent,
    EvmV3ShadowNormalizer,
)
from smart_money.domain.market_identity import ChainId, MarketId
from smart_money.domain.market_state import MarketStateChange, MarketStateCursor

DecodedEventStreamFactory: TypeAlias = Callable[
    [],
    AsyncIterable[DecodedEvmV3PoolEvent],
]


@dataclass(frozen=True, slots=True)
class EvmV3ShadowProvider:
    """Deterministically replay a finite batch of decoded EVM V3 events."""

    normalizer: EvmV3ShadowNormalizer
    event_source_factory: DecodedEventStreamFactory

    def __post_init__(self) -> None:
        if not isinstance(self.normalizer, EvmV3ShadowNormalizer):
            raise TypeError("normalizer must be an EvmV3ShadowNormalizer")
        if not callable(self.event_source_factory):
            raise TypeError("event_source_factory must be callable")

    @property
    def provider_id(self) -> str:
        return self.normalizer.provider_id

    @property
    def chain_id(self) -> ChainId:
        return self.normalizer.chain

    async def stream_state_changes(
        self,
        market: MarketId,
        cursor: MarketStateCursor | None = None,
    ) -> AsyncIterator[MarketStateChange]:
        self._validate_request(market, cursor)
        events_by_position: dict[
            tuple[int, int],
            DecodedEvmV3PoolEvent,
        ] = {}

        async for event in self.event_source_factory():
            if not isinstance(event, DecodedEvmV3PoolEvent):
                raise TypeError(
                    "event source must yield DecodedEvmV3PoolEvent instances"
                )
            position = (event.block_number, event.log_index)
            existing = events_by_position.get(position)
            if existing is None:
                events_by_position[position] = event
            elif existing != event:
                raise ValueError(
                    "conflicting events share the same source position"
                )

        ordered_events = sorted(
            events_by_position.values(),
            key=lambda event: (
                event.block_number,
                event.log_index,
                event.transaction_hash,
            ),
        )
        for event in ordered_events:
            change = self.normalizer.normalize(event)
            if cursor is None or change.ordering_key[:2] > cursor.ordering_key:
                yield change

    def _validate_request(
        self,
        market: MarketId,
        cursor: MarketStateCursor | None,
    ) -> None:
        if not isinstance(market, MarketId):
            raise TypeError("market must be a MarketId")
        if market.canonical_id != self.normalizer.market.canonical_id:
            raise ValueError("market does not match the provider binding")
        if cursor is None:
            return
        if not isinstance(cursor, MarketStateCursor):
            raise TypeError("cursor must be a MarketStateCursor or None")
        if cursor.provider_id != self.provider_id:
            raise ValueError("cursor provider_id does not match provider")
        if cursor.chain.canonical_id != self.chain_id.canonical_id:
            raise ValueError("cursor chain does not match provider")


__all__ = ["DecodedEventStreamFactory", "EvmV3ShadowProvider"]
