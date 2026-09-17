import pytest

from smart_money.application.seeded_discovery import DiscoverySeed, scan_seed


def test_bsc_seed_is_not_sent_to_solana():
    with pytest.raises(ValueError, match="EVM address"):
        DiscoverySeed("solana", "0x2c26f58bba087d83c43c19b4761042320c5beaf4")
    seed = DiscoverySeed("bsc", "0x2c26f58bba087d83c43c19b4761042320c5beaf4")
    result = scan_seed(seed, lambda _: ({"wallet": "0xabc"}, {"wallet": "0xabc"}))
    assert result[0]["event_count"] == 2
