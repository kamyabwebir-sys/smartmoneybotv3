from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal

import pytest

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
    MarketStateChange,
    MarketStateChangeType,
    MarketStateCursor,
    make_market_state_change,
)


def _market(chain: ChainId, venue: str = "uniswap-v3") -> MarketId:
    return MarketId(
        venue=VenueId(venue),
        pair=PairId(
            base=AssetId("ETH", chain),
            quote=AssetId("USDC", chain, "0xA0b8"),
        ),
    )


def _swap(
    chain: ChainId,
    *,
    sequence: int = 100,
    event_index: int = 0,
) -> MarketStateChange:
    return make_market_state_change(
        source_id="evm.shadow.v1",
        source_event_id=f"0xtransaction-{sequence}-{event_index}",
        chain=chain,
        market=_market(chain),
        change_type=MarketStateChangeType.SWAP,
        occurred_at=1_700_000_000,
        chain_sequence=sequence,
        event_index=event_index,
        base_delta="1.25",
        quote_delta="-2500",
    )


def test_base_and_robinhood_have_distinct_canonical_event_identities() -> None:
    base = _swap(ChainId("eip155", "8453"))
    robinhood = _swap(ChainId("eip155", "4663"))

    assert base.chain.reference == "8453"
    assert robinhood.chain.reference == "4663"
    assert base.event_id != robinhood.event_id
    assert base.market.canonical_id != robinhood.market.canonical_id


def test_solana_addresses_remain_case_sensitive_in_unified_events() -> None:
    chain = ChainId("solana", "mainnet-beta")

    def solana_event(address: str) -> MarketStateChange:
        market = MarketId(
            venue=VenueId("raydium"),
            pair=PairId(
                base=AssetId("SOL", chain),
                quote=AssetId("USDC", chain, address),
            ),
        )
        return make_market_state_change(
            source_id="solana.shadow.v1",
            source_event_id="TransactionSignature",
            chain=chain,
            market=market,
            change_type=MarketStateChangeType.SWAP,
            occurred_at=1_700_000_000,
            chain_sequence=200,
            event_index=0,
            base_delta="1",
            quote_delta="-100",
        )

    mixed_case = solana_event("AbCd123")
    lower_case = solana_event("abcd123")

    assert mixed_case.market.pair.quote.contract_address == "AbCd123"
    assert mixed_case.event_id != lower_case.event_id


def test_state_change_is_deterministic_frozen_and_slotted() -> None:
    chain = ChainId(" EIP155 ", " 8453 ")
    first = _swap(chain)
    second = _swap(ChainId("eip155", "8453"))

    assert first == second
    assert first.event_id == second.event_id
    assert first.ordering_key == (100, 0, first.event_id)
    assert not hasattr(first, "__dict__")
    with pytest.raises(FrozenInstanceError):
        first.base_delta = Decimal("2")  # type: ignore[misc]
    with pytest.raises(ValueError, match="event_id"):
        replace(first, event_id="market_state_change_forged")


@pytest.mark.parametrize(
    ("change_type", "base_delta", "quote_delta", "liquidity_delta", "message"),
    [
        (MarketStateChangeType.SWAP, "1", "2", "0", "opposite signs"),
        (MarketStateChangeType.SWAP, "1", "-2", "1", "must be zero"),
        (MarketStateChangeType.LIQUIDITY_ADD, "1", "1", "0", "positive"),
        (MarketStateChangeType.LIQUIDITY_REMOVE, "-1", "-1", "1", "negative"),
    ],
)
def test_state_change_semantics_fail_closed(
    change_type,
    base_delta,
    quote_delta,
    liquidity_delta,
    message,
) -> None:
    chain = ChainId("eip155", "8453")

    with pytest.raises(ValueError, match=message):
        make_market_state_change(
            source_id="evm.shadow.v1",
            source_event_id="0xtransaction",
            chain=chain,
            market=_market(chain),
            change_type=change_type,
            occurred_at=1_700_000_000,
            chain_sequence=100,
            event_index=0,
            base_delta=base_delta,
            quote_delta=quote_delta,
            liquidity_delta=liquidity_delta,
        )


def test_cross_chain_market_is_rejected() -> None:
    base = ChainId("eip155", "8453")

    with pytest.raises(ValueError, match="state-change chain"):
        make_market_state_change(
            source_id="evm.shadow.v1",
            source_event_id="0xtransaction",
            chain=ChainId("eip155", "4663"),
            market=_market(base),
            change_type=MarketStateChangeType.SWAP,
            occurred_at=1_700_000_000,
            chain_sequence=100,
            event_index=0,
            base_delta="1",
            quote_delta="-2",
        )


def test_float_amounts_are_rejected() -> None:
    chain = ChainId("eip155", "8453")

    with pytest.raises(TypeError, match="float"):
        make_market_state_change(
            source_id="evm.shadow.v1",
            source_event_id="0xtransaction",
            chain=chain,
            market=_market(chain),
            change_type=MarketStateChangeType.SWAP,
            occurred_at=1_700_000_000,
            chain_sequence=100,
            event_index=0,
            base_delta=1.25,  # type: ignore[arg-type]
            quote_delta="-2500",
        )


def test_cursor_identity_is_provider_and_chain_scoped() -> None:
    base = MarketStateCursor("evm.shadow.v1", ChainId("eip155", "8453"), 10, 2)
    robinhood = MarketStateCursor(
        "evm.shadow.v1",
        ChainId("eip155", "4663"),
        10,
        2,
    )

    assert base.ordering_key == (10, 2)
    assert base.canonical_id != robinhood.canonical_id
    assert not hasattr(base, "__dict__")


class _FakeUnifiedProvider:
    def __init__(
        self,
        chain_id: ChainId,
        events: tuple[MarketStateChange, ...],
    ) -> None:
        self.provider_id = "evm.shadow.v1"
        self.chain_id = chain_id
        self._events = tuple(sorted(events, key=lambda item: item.ordering_key))

    async def stream_state_changes(
        self,
        market: MarketId,
        cursor: MarketStateCursor | None = None,
    ):
        assert market.pair.base.chain == self.chain_id
        for event in self._events:
            if cursor is None or event.ordering_key[:2] > cursor.ordering_key:
                yield event


@pytest.mark.asyncio
async def test_unified_provider_port_streams_in_deterministic_order() -> None:
    chain = ChainId("eip155", "8453")
    later = _swap(chain, sequence=101)
    earlier = _swap(chain, sequence=100)
    provider = _FakeUnifiedProvider(chain, (later, earlier))

    assert isinstance(provider, UnifiedMarketProvider)
    streamed = tuple(
        [
            event
            async for event in provider.stream_state_changes(
                _market(chain),
                MarketStateCursor(provider.provider_id, chain, 99, 0),
            )
        ]
    )

    assert streamed == (earlier, later)
