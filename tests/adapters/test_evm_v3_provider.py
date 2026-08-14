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
from smart_money.domain.market_state import MarketStateCursor

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
