import pytest

from smart_money.application.first_liquidity_detection import detect_first_liquidity
from smart_money.application.token_metadata_observation import build_token_metadata_observation


def test_metadata_observation_is_deterministic() -> None:
    item = build_token_metadata_observation("solana:mainnet-beta:t", "Token", "TKN", 9, "rpc", 10)
    assert item.canonical_dict()["token_id"] == "solana:mainnet-beta:t"
    assert item.observation_id == build_token_metadata_observation("solana:mainnet-beta:t", "Token", "TKN", 9, "rpc", 10).observation_id


def test_first_liquidity_requires_positive_units() -> None:
    item = detect_first_liquidity("solana:mainnet-beta:t", "pool-1", 100, 11, "rpc")
    assert item.liquidity_units == 100
    with pytest.raises(ValueError):
        detect_first_liquidity("t", "p", 0, 1, "rpc")
