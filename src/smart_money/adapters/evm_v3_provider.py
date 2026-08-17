from __future__ import annotations

from collections.abc import AsyncIterable, AsyncIterator, Callable
from dataclasses import dataclass
from typing import TypeAlias

from smart_money.adapters.evm_v3_shadow import (
    DecodedEvmV3PoolEvent,
    EvmV3ShadowNormalizer,
)
from smart_money.domain.market_identity import ChainId, MarketId
from smart_money.domain.market_state import (
    MarketStateChange,
    MarketStateCheckpoint,
    MarketStateCursor,
    make_market_state_checkpoint,
)

DecodedEventStreamFactory: TypeAlias = Callable[
    [],
    AsyncIterable[DecodedEvmV3PoolEvent],
]
ResumableDecodedEventStreamFactory: TypeAlias = Callable[
    [int | None],
    AsyncIterable[DecodedEvmV3PoolEvent],
]


@dataclass(frozen=True, slots=True)
class EvmV3ShadowProvider:
    """Order decoded V3 events with a deterministic block watermark."""

    normalizer: EvmV3ShadowNormalizer
    event_source_factory: DecodedEventStreamFactory
    reorder_window_blocks: int = 64
    max_buffered_events: int = 10_000
    resumable_event_source_factory: ResumableDecodedEventStreamFactory | None = (
        None
    )

    def __post_init__(self) -> None:
        if not isinstance(self.normalizer, EvmV3ShadowNormalizer):
            raise TypeError("normalizer must be an EvmV3ShadowNormalizer")
        if not callable(self.event_source_factory):
            raise TypeError("event_source_factory must be callable")
        if (
            self.resumable_event_source_factory is not None
            and not callable(self.resumable_event_source_factory)
        ):
            raise TypeError("resumable_event_source_factory must be callable")
        self._require_non_negative_integer(
            self.reorder_window_blocks,
            "reorder_window_blocks",
        )
        self._require_positive_integer(
            self.max_buffered_events,
            "max_buffered_events",
        )

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
        highest_seen_block = -1
        committed_watermark = -1

        async for event in self.event_source_factory():
            if not isinstance(event, DecodedEvmV3PoolEvent):
                raise TypeError(
                    "event source must yield DecodedEvmV3PoolEvent instances"
                )
            if event.block_number <= committed_watermark:
                raise ValueError(
                    "late event is at or behind the committed watermark"
                )
            highest_seen_block = max(highest_seen_block, event.block_number)
            next_watermark = (
                highest_seen_block - self.reorder_window_blocks - 1
            )
            if next_watermark > committed_watermark:
                async for change in self._flush_through(
                    events_by_position,
                    next_watermark,
                    cursor,
                ):
                    yield change
                committed_watermark = next_watermark

            position = (event.block_number, event.log_index)
            existing = events_by_position.get(position)
            if existing is None:
                if len(events_by_position) >= self.max_buffered_events:
                    raise BufferError("event reorder buffer capacity exceeded")
                events_by_position[position] = event
            elif existing != event:
                raise ValueError(
                    "conflicting events share the same source position"
                )

        async for change in self._flush_through(
            events_by_position,
            None,
            cursor,
        ):
            yield change

    def checkpoint_for(
        self,
        change: MarketStateChange,
    ) -> MarketStateCheckpoint:
        if not isinstance(change, MarketStateChange):
            raise TypeError("change must be a MarketStateChange")
        if change.source_id != self.provider_id:
            raise ValueError("change source_id does not match provider")
        if change.chain.canonical_id != self.chain_id.canonical_id:
            raise ValueError("change chain does not match provider")
        if change.market.canonical_id != self.normalizer.market.canonical_id:
            raise ValueError("change market does not match provider")
        return make_market_state_checkpoint(
            provider_id=self.provider_id,
            chain=self.chain_id,
            market=self.normalizer.market,
            cursor=MarketStateCursor(
                provider_id=self.provider_id,
                chain=self.chain_id,
                chain_sequence=change.chain_sequence,
                event_index=change.event_index,
            ),
            reorder_window_blocks=self.reorder_window_blocks,
        )

    def stream_from_checkpoint(
        self,
        checkpoint: MarketStateCheckpoint,
    ) -> AsyncIterator[MarketStateChange]:
        self._validate_checkpoint(checkpoint)
        if self.resumable_event_source_factory is None:
            event_source_factory = self.event_source_factory
        else:
            resumable_factory = self.resumable_event_source_factory

            def event_source_factory() -> AsyncIterable[
                DecodedEvmV3PoolEvent
            ]:
                return resumable_factory(checkpoint.source_watermark)

        resumed_provider = EvmV3ShadowProvider(
            normalizer=self.normalizer,
            event_source_factory=event_source_factory,
            reorder_window_blocks=self.reorder_window_blocks,
            max_buffered_events=self.max_buffered_events,
            resumable_event_source_factory=self.resumable_event_source_factory,
        )
        return resumed_provider.stream_state_changes(
            checkpoint.market,
            checkpoint.cursor,
        )

    async def _flush_through(
        self,
        events_by_position: dict[
            tuple[int, int],
            DecodedEvmV3PoolEvent,
        ],
        watermark: int | None,
        cursor: MarketStateCursor | None,
    ) -> AsyncIterator[MarketStateChange]:
        ready_positions = sorted(
            position
            for position in events_by_position
            if watermark is None or position[0] <= watermark
        )
        for position in ready_positions:
            event = events_by_position.pop(position)
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

    def _validate_checkpoint(
        self,
        checkpoint: MarketStateCheckpoint,
    ) -> None:
        if not isinstance(checkpoint, MarketStateCheckpoint):
            raise TypeError("checkpoint must be a MarketStateCheckpoint")
        if checkpoint.provider_id != self.provider_id:
            raise ValueError("checkpoint provider_id does not match provider")
        if checkpoint.chain.canonical_id != self.chain_id.canonical_id:
            raise ValueError("checkpoint chain does not match provider")
        if (
            checkpoint.market.canonical_id
            != self.normalizer.market.canonical_id
        ):
            raise ValueError("checkpoint market does not match provider")
        if checkpoint.reorder_window_blocks != self.reorder_window_blocks:
            raise ValueError("checkpoint reorder window does not match provider")

    @staticmethod
    def _require_non_negative_integer(value: object, field_name: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{field_name} must be an integer")
        if value < 0:
            raise ValueError(f"{field_name} must be non-negative")
        return value

    @staticmethod
    def _require_positive_integer(value: object, field_name: str) -> int:
        result = EvmV3ShadowProvider._require_non_negative_integer(
            value,
            field_name,
        )
        if result == 0:
            raise ValueError(f"{field_name} must be positive")
        return result


__all__ = [
    "DecodedEventStreamFactory",
    "EvmV3ShadowProvider",
    "ResumableDecodedEventStreamFactory",
]
