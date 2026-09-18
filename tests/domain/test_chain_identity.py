from dataclasses import FrozenInstanceError

import pytest

from smart_money.domain.chain_identity import (
    PoolId,
    TokenId,
    WalletId,
    canonical_chain_namespace,
    detect_identity_conflict,
    parse_identity_namespace,
)
from smart_money.domain.market_identity import ChainId


def test_chain_aware_ids_are_immutable_and_deterministic() -> None:
    chain = ChainId("eip155", "8453")
    wallet = WalletId(chain, " 0xAbC ")
    token0 = TokenId(chain, "0xToken0")
    token1 = TokenId(chain, "0xToken1")
    pool = PoolId(chain, "0xPool", token0, token1)
    assert wallet.address == "0xabc"
    assert wallet.canonical_id == WalletId(chain, "0xABC").canonical_id
    assert token0.canonical_id == TokenId(chain, "0xTOKEN0").canonical_id
    assert pool.canonical_id == PoolId(chain, "0xpool", token0, token1).canonical_id
    with pytest.raises(FrozenInstanceError):
        wallet.address = "changed"  # type: ignore[misc]


def test_identity_rejects_cross_chain_pool_and_invalid_addresses() -> None:
    base = ChainId("eip155", "8453")
    solana = ChainId("solana", "mainnet-beta")
    with pytest.raises(ValueError, match="pool tokens"):
        PoolId(base, "pool", TokenId(base, "a"), TokenId(solana, "b"))
    with pytest.raises(ValueError, match="without whitespace"):
        WalletId(base, "0x bad")


def test_identity_namespace_is_chain_aware_and_collision_safe() -> None:
    base = ChainId("eip155", "8453")
    solana = ChainId("solana", "mainnet-beta")
    assert canonical_chain_namespace(base) == "evm:base"
    assert WalletId(base, "0xAbC").namespace == "evm:base:0xabc"
    assert TokenId(solana, "DezX").namespace == "solana:mainnet-beta:DezX"
    assert WalletId(base, "same").namespace != WalletId(solana, "same").namespace


def test_identity_namespace_parser_supports_canonical_and_legacy_reads() -> None:
    parsed = parse_identity_namespace("evm:base:0xabc", kind="wallet")
    assert parsed.chain == ChainId("eip155", "8453")
    assert parsed.address == "0xabc"
    assert parsed.legacy is False
    legacy = parse_identity_namespace("legacy-wallet-id", kind="wallet")
    assert legacy.chain is None
    assert legacy.legacy is True


def test_identity_conflict_detection_fails_closed() -> None:
    base = parse_identity_namespace("evm:base:0xabc", kind="wallet")
    solana = parse_identity_namespace("solana:mainnet-beta:0xabc", kind="wallet")
    assert detect_identity_conflict(base, solana).code == "chain_mismatch"
    other = parse_identity_namespace("evm:base:0xdef", kind="wallet")
    assert detect_identity_conflict(base, other).code == "address_collision"
    legacy = parse_identity_namespace("legacy-wallet-id", kind="wallet")
    assert detect_identity_conflict(legacy, base).code == "legacy_identity_mismatch"
    assert detect_identity_conflict(base, base) is None
