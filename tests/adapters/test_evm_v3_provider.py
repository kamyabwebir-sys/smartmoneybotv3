from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from smart_money.adapters.evm_v3_provider import EvmV3ShadowProvider
from smart_money.adapters.evm_v3_shadow import (
    DecodedEvmV3PoolEvent,
    EvmV3PoolEventType,
    EvmV3ShadowNormalizer,
)
from smart_money.application.ports.unified_market_provider import (
    UnifiedMarketProvider,
)
from smart_money.domain.market_identity import (
    AssetId,
    ChainId,
    MarketId,
    PairId,
    VenueId,
)
from smart_money.domain.market_state import (
    MarketStateCheckpoint,
    MarketStateCursor,
    make_market_state_checkpoint,
)

_POOL_ADDRESS = f"0x{'1' * 40}"
_TOKEN0_ADDRESS = f"0x{'a' * 40}"
_TOKEN1_ADDRESS = f"0x{'b' * 40}"


def _normalizer(
    chain: ChainId = ChainId("eip155", "8453"),
) -> EvmV3ShadowNormalizer:
    token0 = AssetId("USDC", chain, _TOKEN0_ADDRESS)
    token1 = AssetId("WETH", chain, _TOKEN1_ADDRESS)
    market = MarketId(VenueId("uniswap-v3"), PairId(token1, token0))
    return EvmV3ShadowNormalizer(
        provider_id="evm.shadow.v3",
        chain=chain,
        pool_address=_POOL_ADDRESS,
        market=market,
        token0=token0,
        token1=token1,
    )


def _event(
    block_number: int,
    log_index: int,
    *,
    transaction_marker: str = "c",
    amount0: str = "100",
    amount1: str = "-1",
) -> DecodedEvmV3PoolEvent:
    return DecodedEvmV3PoolEvent(
        event_type=EvmV3PoolEventType.SWAP,
        transaction_hash=f"0x{transaction_marker * 64}",
        emitter_address=_POOL_ADDRESS,
        block_number=block_number,
        log_index=log_index,
        block_timestamp=1_700_000_000 + block_number,
        amount0=amount0,
        amount1=amount1,
    )


def _factory(events: tuple[Any, ...], calls: list[int] | None = None):
    def create_stream():
        if calls is not None:
            calls.append(1)

        async def stream():
            for event in events:
                yield event

        return stream()

    return create_stream


async def _collect(provider, market, cursor=None):
    return tuple(
        [
            event
            async for event in provider.stream_state_changes(market, cursor)
        ]
    )


@pytest.mark.asyncio
async def test_provider_sorts_deduplicates_and_replays_stably() -> None:
    normalizer = _normalizer()
    earlier = _event(100, 2, transaction_marker="a")
    later = _event(101, 0, transaction_marker="b")
    calls: list[int] = []
    provider = EvmV3ShadowProvider(
        normalizer,
        _factory((later, earlier, earlier), calls),
    )

    first = await _collect(provider, normalizer.market)
    second = await _collect(provider, normalizer.market)

    assert isinstance(provider, UnifiedMarketProvider)
    assert provider.provider_id == normalizer.provider_id
    assert provider.chain_id == normalizer.chain
    assert tuple(item.ordering_key[:2] for item in first) == ((100, 2), (101, 0))
    assert first == second
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_windowed_provider_emits_before_live_source_completion() -> None:
    normalizer = _normalizer()
    source_progress: list[int] = []

    async def live_source():
        for event in (
            _event(101, 0, transaction_marker="b"),
            _event(100, 2, transaction_marker="a"),
            _event(102, 0, transaction_marker="c"),
            _event(103, 0, transaction_marker="d"),
        ):
            source_progress.append(event.block_number)
            yield event

    provider = EvmV3ShadowProvider(
        normalizer,
        live_source,
        reorder_window_blocks=1,
    )
    stream = provider.stream_state_changes(normalizer.market)

    first = await anext(stream)

    assert first.ordering_key[:2] == (100, 2)
    assert source_progress == [101, 100, 102]
    await stream.aclose()


@pytest.mark.asyncio
async def test_windowed_provider_rejects_event_behind_watermark() -> None:
    normalizer = _normalizer()
    provider = EvmV3ShadowProvider(
        normalizer,
        _factory(
            (
                _event(100, 0, transaction_marker="a"),
                _event(102, 0, transaction_marker="b"),
                _event(100, 1, transaction_marker="c"),
            )
        ),
        reorder_window_blocks=1,
    )

    with pytest.raises(ValueError, match="committed watermark"):
        await _collect(provider, normalizer.market)


@pytest.mark.asyncio
async def test_windowed_provider_fails_closed_at_buffer_capacity() -> None:
    normalizer = _normalizer()
    provider = EvmV3ShadowProvider(
        normalizer,
        _factory(
            (
                _event(100, 0, transaction_marker="a"),
                _event(100, 1, transaction_marker="b"),
                _event(100, 2, transaction_marker="c"),
            )
        ),
        reorder_window_blocks=1,
        max_buffered_events=2,
    )

    with pytest.raises(BufferError, match="capacity"):
        await _collect(provider, normalizer.market)


@pytest.mark.asyncio
async def test_end_of_stream_flushes_open_window_in_canonical_order() -> None:
    normalizer = _normalizer()
    provider = EvmV3ShadowProvider(
        normalizer,
        _factory(
            (
                _event(101, 2, transaction_marker="c"),
                _event(101, 0, transaction_marker="a"),
                _event(100, 5, transaction_marker="b"),
            )
        ),
        reorder_window_blocks=10,
    )

    changes = await _collect(provider, normalizer.market)

    assert tuple(change.ordering_key[:2] for change in changes) == (
        (100, 5),
        (101, 0),
        (101, 2),
    )


@pytest.mark.asyncio
async def test_checkpoint_resumes_after_last_consumed_position() -> None:
    normalizer = _normalizer()
    events = (
        _event(100, 0, transaction_marker="a"),
        _event(100, 1, transaction_marker="b"),
        _event(101, 0, transaction_marker="c"),
    )
    provider = EvmV3ShadowProvider(
        normalizer,
        _factory(events),
        reorder_window_blocks=2,
    )
    first_run = await _collect(provider, normalizer.market)

    checkpoint = provider.checkpoint_for(first_run[1])
    resumed = tuple(
        [
            change
            async for change in provider.stream_from_checkpoint(checkpoint)
        ]
    )

    assert checkpoint.cursor.ordering_key == (100, 1)
    assert checkpoint.source_watermark == 99
    assert resumed == (first_run[2],)


@pytest.mark.asyncio
async def test_checkpoint_passes_safe_watermark_to_resumable_source() -> None:
    normalizer = _normalizer()
    events = (
        _event(100, 0, transaction_marker="a"),
        _event(100, 1, transaction_marker="b"),
        _event(101, 0, transaction_marker="c"),
    )
    watermarks: list[int | None] = []

    def resumable_source(source_watermark: int | None):
        watermarks.append(source_watermark)
        start = -1 if source_watermark is None else source_watermark

        async def stream():
            for event in events:
                if event.block_number >= start:
                    yield event

        return stream()

    provider = EvmV3ShadowProvider(
        normalizer=normalizer,
        event_source_factory=_factory(events),
        reorder_window_blocks=2,
        resumable_event_source_factory=resumable_source,
    )
    checkpoint = provider.checkpoint_for(normalizer.normalize(events[1]))

    resumed = tuple(
        [
            change
            async for change in provider.stream_from_checkpoint(checkpoint)
        ]
    )

    assert watermarks == [99]
    assert tuple(change.ordering_key[:2] for change in resumed) == ((101, 0),)


def test_checkpoint_is_content_addressed_frozen_and_slotted() -> None:
    normalizer = _normalizer()
    provider = EvmV3ShadowProvider(
        normalizer,
        _factory(()),
        reorder_window_blocks=2,
    )
    change = normalizer.normalize(_event(100, 1))

    first = provider.checkpoint_for(change)
    second = provider.checkpoint_for(change)

    assert first == second
    assert first.checkpoint_id == second.checkpoint_id
    assert first.canonical_dict()["checkpoint_id"] == first.checkpoint_id
    assert not hasattr(first, "__dict__")
    with pytest.raises(FrozenInstanceError):
        first.source_watermark = 100  # type: ignore[misc]


def test_checkpoint_at_genesis_uses_no_source_watermark() -> None:
    normalizer = _normalizer()
    provider = EvmV3ShadowProvider(normalizer, _factory(()))
    change = normalizer.normalize(_event(0, 0))

    checkpoint = provider.checkpoint_for(change)

    assert checkpoint.source_watermark is None
    assert checkpoint.cursor.ordering_key == (0, 0)


@pytest.mark.parametrize(
    ("mismatch", "message"),
    [
        ("provider", "provider_id"),
        ("chain", "chain"),
        ("market", "market"),
        ("window", "reorder window"),
    ],
)
def test_provider_rejects_incompatible_checkpoint(
    mismatch: str,
    message: str,
) -> None:
    normalizer = _normalizer()
    provider = EvmV3ShadowProvider(
        normalizer,
        _factory(()),
        reorder_window_blocks=2,
    )
    valid = provider.checkpoint_for(normalizer.normalize(_event(100, 1)))
    checkpoint_provider = valid.provider_id
    checkpoint_chain = valid.chain
    checkpoint_market = valid.market
    checkpoint_window = valid.reorder_window_blocks
    if mismatch == "provider":
        checkpoint_provider = "other.provider"
    elif mismatch == "chain":
        robinhood = _normalizer(ChainId("eip155", "4663"))
        checkpoint_chain = robinhood.chain
        checkpoint_market = robinhood.market
    elif mismatch == "market":
        checkpoint_market = MarketId(
            VenueId("other-v3"),
            normalizer.market.pair,
        )
    else:
        checkpoint_window = 3
    incompatible = make_market_state_checkpoint(
        provider_id=checkpoint_provider,
        chain=checkpoint_chain,
        market=checkpoint_market,
        cursor=MarketStateCursor(
            checkpoint_provider,
            checkpoint_chain,
            100,
            1,
        ),
        reorder_window_blocks=checkpoint_window,
    )

    with pytest.raises(ValueError, match=message):
        provider.stream_from_checkpoint(incompatible)


def test_checkpoint_rejects_forged_identity_and_unsafe_watermark() -> None:
    normalizer = _normalizer()
    cursor = MarketStateCursor(
        "evm.shadow.v3",
        normalizer.chain,
        100,
        1,
    )
    valid = make_market_state_checkpoint(
        provider_id="evm.shadow.v3",
        chain=normalizer.chain,
        market=normalizer.market,
        cursor=cursor,
        reorder_window_blocks=2,
    )
    values = {
        "checkpoint_id": valid.checkpoint_id,
        "provider_id": valid.provider_id,
        "chain": valid.chain,
        "market": valid.market,
        "cursor": valid.cursor,
        "source_watermark": valid.source_watermark,
        "reorder_window_blocks": valid.reorder_window_blocks,
    }

    with pytest.raises(ValueError, match="checkpoint_id"):
        MarketStateCheckpoint(**{**values, "checkpoint_id": "forged"})
    with pytest.raises(ValueError, match="cursor-safe"):
        MarketStateCheckpoint(**{**values, "source_watermark": 100})


@pytest.mark.asyncio
async def test_provider_filters_positions_at_or_before_cursor() -> None:
    normalizer = _normalizer()
    provider = EvmV3ShadowProvider(
        normalizer,
        _factory((_event(101, 0), _event(100, 2))),
    )
    cursor = MarketStateCursor(
        provider.provider_id,
        provider.chain_id,
        chain_sequence=100,
        event_index=2,
    )

    changes = await _collect(provider, normalizer.market, cursor)

    assert tuple(item.ordering_key[:2] for item in changes) == ((101, 0),)


@pytest.mark.asyncio
async def test_provider_rejects_source_position_collision() -> None:
    normalizer = _normalizer()
    provider = EvmV3ShadowProvider(
        normalizer,
        _factory(
            (
                _event(100, 2, transaction_marker="a"),
                _event(100, 2, transaction_marker="b"),
            )
        ),
    )

    with pytest.raises(ValueError, match="same source position"):
        await _collect(provider, normalizer.market)


@pytest.mark.asyncio
async def test_provider_rejects_wrong_market_before_opening_source() -> None:
    normalizer = _normalizer()
    calls: list[int] = []
    provider = EvmV3ShadowProvider(normalizer, _factory((), calls))
    other_market = MarketId(
        VenueId("other-v3"),
        normalizer.market.pair,
    )

    with pytest.raises(ValueError, match="market"):
        await _collect(provider, other_market)

    assert calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("cursor", "message"),
    [
        (
            MarketStateCursor(
                "other.provider",
                ChainId("eip155", "8453"),
                0,
                0,
            ),
            "provider_id",
        ),
        (
            MarketStateCursor(
                "evm.shadow.v3",
                ChainId("eip155", "4663"),
                0,
                0,
            ),
            "chain",
        ),
    ],
)
async def test_provider_rejects_mismatched_cursor(
    cursor: MarketStateCursor,
    message: str,
) -> None:
    normalizer = _normalizer()
    provider = EvmV3ShadowProvider(normalizer, _factory(()))

    with pytest.raises(ValueError, match=message):
        await _collect(provider, normalizer.market, cursor)


@pytest.mark.asyncio
async def test_provider_rejects_non_decoded_source_items() -> None:
    normalizer = _normalizer()
    provider = EvmV3ShadowProvider(normalizer, _factory((object(),)))

    with pytest.raises(TypeError, match="DecodedEvmV3PoolEvent"):
        await _collect(provider, normalizer.market)


def test_provider_is_frozen_and_slotted() -> None:
    normalizer = _normalizer()
    provider = EvmV3ShadowProvider(normalizer, _factory(()))

    assert not hasattr(provider, "__dict__")
    with pytest.raises(FrozenInstanceError):
        provider.normalizer = normalizer  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("reorder_window_blocks", -1, "non-negative"),
        ("reorder_window_blocks", True, "integer"),
        ("max_buffered_events", 0, "positive"),
        ("max_buffered_events", 1.5, "integer"),
    ],
)
def test_provider_rejects_invalid_window_configuration(
    field: str,
    value: object,
    message: str,
) -> None:
    normalizer = _normalizer()
    values = {
        "normalizer": normalizer,
        "event_source_factory": _factory(()),
        field: value,
    }

    with pytest.raises((TypeError, ValueError), match=message):
        EvmV3ShadowProvider(**values)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_base_and_robinhood_streams_remain_chain_distinct() -> None:
    base_normalizer = _normalizer(ChainId("eip155", "8453"))
    robinhood_normalizer = _normalizer(ChainId("eip155", "4663"))
    event = _event(100, 2)
    base = EvmV3ShadowProvider(base_normalizer, _factory((event,)))
    robinhood = EvmV3ShadowProvider(
        robinhood_normalizer,
        _factory((event,)),
    )

    base_change = (await _collect(base, base_normalizer.market))[0]
    robinhood_change = (
        await _collect(robinhood, robinhood_normalizer.market)
    )[0]

    assert base_change.chain != robinhood_change.chain
    assert base_change.event_id != robinhood_change.event_id
