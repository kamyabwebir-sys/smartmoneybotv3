from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from smart_money.adapters.evm_v3_shadow import (
    DecodedEvmV3PoolEvent,
    EvmV3PoolEventType,
    EvmV3ShadowNormalizer,
)
from smart_money.domain.market_identity import (
    AssetId,
    ChainId,
    MarketId,
    PairId,
    VenueId,
)
from smart_money.domain.market_state import MarketStateChangeType

_BASE_ADDRESS = f"0x{'b' * 40}"
_QUOTE_ADDRESS = f"0x{'a' * 40}"
_POOL_ADDRESS = f"0x{'1' * 40}"
_TRANSACTION_HASH = f"0x{'c' * 64}"


def _binding(
    chain: ChainId = ChainId("eip155", "8453"),
) -> tuple[EvmV3ShadowNormalizer, AssetId, AssetId]:
    base = AssetId("WETH", chain, _BASE_ADDRESS)
    quote = AssetId("USDC", chain, _QUOTE_ADDRESS)
    market = MarketId(VenueId("uniswap-v3"), PairId(base, quote))
    return (
        EvmV3ShadowNormalizer(
            provider_id="EVM.Shadow.V3",
            chain=chain,
            pool_address=_POOL_ADDRESS,
            market=market,
            token0=quote,
            token1=base,
        ),
        base,
        quote,
    )


def _event(
    event_type: EvmV3PoolEventType,
    *,
    amount0: Decimal | int | str,
    amount1: Decimal | int | str,
    liquidity_amount: Decimal | int | str = "0",
) -> DecodedEvmV3PoolEvent:
    return DecodedEvmV3PoolEvent(
        event_type=event_type,
        transaction_hash=f"  0x{'C' * 64}  ",
        emitter_address=f"  0x{'1' * 40}  ",
        block_number=100,
        log_index=2,
        block_timestamp=1_700_000_000,
        amount0=amount0,
        amount1=amount1,
        liquidity_amount=liquidity_amount,
    )


def test_swap_maps_token_order_to_market_order_deterministically() -> None:
    normalizer, _, _ = _binding()
    decoded = _event(
        EvmV3PoolEventType.SWAP,
        amount0="2500",
        amount1="-1.25",
    )

    first = normalizer.normalize(decoded)
    second = normalizer.normalize(decoded)

    assert first == second
    assert first.change_type is MarketStateChangeType.SWAP
    assert first.base_delta == Decimal("-1.25")
    assert first.quote_delta == Decimal("2500")
    assert first.liquidity_delta == 0
    assert first.source_id == "evm.shadow.v3"
    assert first.source_event_id == f"{_POOL_ADDRESS}:{_TRANSACTION_HASH}"
    assert first.ordering_key[:2] == (100, 2)


def test_mint_maps_to_positive_pool_and_liquidity_deltas() -> None:
    normalizer, _, _ = _binding()

    change = normalizer.normalize(
        _event(
            EvmV3PoolEventType.MINT,
            amount0="1000",
            amount1="0.5",
            liquidity_amount="400",
        )
    )

    assert change.change_type is MarketStateChangeType.LIQUIDITY_ADD
    assert change.base_delta == Decimal("0.5")
    assert change.quote_delta == Decimal("1000")
    assert change.liquidity_delta == Decimal("400")


def test_burn_maps_unsigned_event_amounts_to_negative_pool_deltas() -> None:
    normalizer, _, _ = _binding()

    change = normalizer.normalize(
        _event(
            EvmV3PoolEventType.BURN,
            amount0="800",
            amount1="0.4",
            liquidity_amount="300",
        )
    )

    assert change.change_type is MarketStateChangeType.LIQUIDITY_REMOVE
    assert change.base_delta == Decimal("-0.4")
    assert change.quote_delta == Decimal("-800")
    assert change.liquidity_delta == Decimal("-300")


def test_chain_identity_participates_in_normalized_event_id() -> None:
    base, _, _ = _binding(ChainId("eip155", "8453"))
    robinhood, _, _ = _binding(ChainId("eip155", "4663"))
    event = _event(
        EvmV3PoolEventType.SWAP,
        amount0="100",
        amount1="-1",
    )

    assert base.normalize(event).event_id != robinhood.normalize(event).event_id


def test_decoded_event_and_normalizer_are_frozen_and_slotted() -> None:
    normalizer, _, _ = _binding()
    event = _event(
        EvmV3PoolEventType.SWAP,
        amount0="100",
        amount1="-1",
    )

    assert not hasattr(normalizer, "__dict__")
    assert not hasattr(event, "__dict__")
    with pytest.raises(FrozenInstanceError):
        event.log_index = 3  # type: ignore[misc]


@pytest.mark.parametrize(
    ("event_type", "amount0", "amount1", "liquidity", "message"),
    [
        (EvmV3PoolEventType.SWAP, "1", "2", "0", "opposite signs"),
        (EvmV3PoolEventType.SWAP, "1", "-2", "3", "must be zero"),
        (EvmV3PoolEventType.MINT, "-1", "2", "3", "non-negative"),
        (EvmV3PoolEventType.MINT, "0", "0", "3", "non-zero token"),
        (EvmV3PoolEventType.BURN, "1", "2", "0", "must be positive"),
    ],
)
def test_decoded_event_semantics_fail_closed(
    event_type,
    amount0,
    amount1,
    liquidity,
    message,
) -> None:
    with pytest.raises(ValueError, match=message):
        _event(
            event_type,
            amount0=amount0,
            amount1=amount1,
            liquidity_amount=liquidity,
        )


def test_float_amounts_are_rejected() -> None:
    with pytest.raises(TypeError, match="float"):
        _event(
            EvmV3PoolEventType.SWAP,
            amount0=1.0,  # type: ignore[arg-type]
            amount1="-2",
        )


def test_normalizer_rejects_non_evm_and_mismatched_pool_bindings() -> None:
    solana = ChainId("solana", "mainnet-beta")
    sol = AssetId("SOL", solana)
    usdc = AssetId("USDC", solana, "TokenAddress")

    with pytest.raises(ValueError, match="eip155"):
        EvmV3ShadowNormalizer(
            "evm.shadow.v3",
            solana,
            _POOL_ADDRESS,
            MarketId(VenueId("raydium"), PairId(sol, usdc)),
            sol,
            usdc,
        )

    normalizer, base, quote = _binding()
    unrelated = AssetId("DAI", normalizer.chain, f"0x{'d' * 40}")
    with pytest.raises(ValueError, match="market pair"):
        EvmV3ShadowNormalizer(
            normalizer.provider_id,
            normalizer.chain,
            normalizer.pool_address,
            normalizer.market,
            quote,
            unrelated,
        )
    assert base.canonical_id != unrelated.canonical_id


def test_normalizer_rejects_event_from_another_pool() -> None:
    normalizer, _, _ = _binding()
    event = DecodedEvmV3PoolEvent(
        event_type=EvmV3PoolEventType.SWAP,
        transaction_hash=_TRANSACTION_HASH,
        emitter_address=f"0x{'2' * 40}",
        block_number=100,
        log_index=2,
        block_timestamp=1_700_000_000,
        amount0="100",
        amount1="-1",
    )

    with pytest.raises(ValueError, match="bound pool"):
        normalizer.normalize(event)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("transaction_hash", "0xabc", "32-byte"),
        ("emitter_address", "0xabc", "20-byte"),
    ],
)
def test_decoded_event_rejects_malformed_evm_references(
    field,
    value,
    message,
) -> None:
    values = {
        "event_type": EvmV3PoolEventType.SWAP,
        "transaction_hash": _TRANSACTION_HASH,
        "emitter_address": _POOL_ADDRESS,
        "block_number": 100,
        "log_index": 2,
        "block_timestamp": 1_700_000_000,
        "amount0": "100",
        "amount1": "-1",
    }
    values[field] = value

    with pytest.raises(ValueError, match=message):
        DecodedEvmV3PoolEvent(**values)
