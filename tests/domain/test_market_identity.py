from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from smart_money.domain.market_identity import (
    AssetId,
    ChainId,
    MarketId,
    PairId,
    VenueId,
    normalize_symbol,
)


def test_market_identity_is_normalized_and_deterministic() -> None:
    first = MarketId(
        venue=VenueId("  Base-DEX "),
        pair=PairId(
            base=AssetId(
                " eth ",
                ChainId(" EIP155 ", " 8453 "),
                " 0xAbCd ",
            ),
            quote=AssetId(
                "usdc",
                ChainId("eip155", "8453"),
                "0x1234",
            ),
        ),
    )
    second = MarketId(
        venue=VenueId("base-dex"),
        pair=PairId(
            base=AssetId("ETH", ChainId("eip155", "8453"), "0xabcd"),
            quote=AssetId("USDC", ChainId("eip155", "8453"), "0x1234"),
        ),
    )

    assert first == second
    assert first.canonical_id == second.canonical_id
    assert first.pair.base.symbol == "ETH"
    assert first.pair.base.contract_address == "0xabcd"
    assert first.schema_version == "market_id.v1"


def test_solana_contract_identity_preserves_case() -> None:
    chain = ChainId("solana", "mainnet-beta")

    first = AssetId("token", chain, "AbCd123")
    second = AssetId("token", chain, "abcd123")

    assert first.contract_address == "AbCd123"
    assert first.canonical_id != second.canonical_id


@pytest.mark.parametrize(
    "symbol",
    ["", " ", "ETH/USD", "نماد", "A" * 33],
)
def test_invalid_symbols_fail_closed(symbol: str) -> None:
    with pytest.raises(ValueError, match="canonical asset symbol syntax"):
        normalize_symbol(symbol)


def test_contract_address_requires_chain_identity() -> None:
    with pytest.raises(ValueError, match="requires chain identity"):
        AssetId("USDC", contract_address="0x1234")


def test_pair_rejects_identical_assets() -> None:
    asset = AssetId("SOL", ChainId("solana", "mainnet-beta"))

    with pytest.raises(ValueError, match="must be different"):
        PairId(asset, asset)


@pytest.mark.parametrize(
    "model",
    [
        ChainId("solana", "mainnet-beta"),
        VenueId("solana-dex"),
        AssetId("SOL", ChainId("solana", "mainnet-beta")),
        PairId(
            AssetId("SOL", ChainId("solana", "mainnet-beta")),
            AssetId("USDC", ChainId("solana", "mainnet-beta"), "CaseSensitive"),
        ),
        MarketId(
            VenueId("solana-dex"),
            PairId(
                AssetId("SOL", ChainId("solana", "mainnet-beta")),
                AssetId(
                    "USDC",
                    ChainId("solana", "mainnet-beta"),
                    "CaseSensitive",
                ),
            ),
        ),
    ],
)
def test_market_identity_models_are_frozen_and_slotted(model: object) -> None:
    model_type = type(model)

    assert is_dataclass(model_type)
    assert model_type.__dataclass_params__.frozen is True
    assert hasattr(model_type, "__slots__")

    field_name = next(iter(model_type.__dataclass_fields__))
    with pytest.raises((FrozenInstanceError, AttributeError)):
        setattr(model, field_name, getattr(model, field_name))
