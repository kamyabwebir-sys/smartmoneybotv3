import pytest
from smart_money.ingestion.binance_provider import BinanceProvider
from smart_money.ingestion.contracts import IngestionCandle


def test_binance_mapping_logic():
    provider = BinanceProvider()
    # Sample raw kline from Binance API
    raw_kline = [
        1625097600000,
        "35000.00",
        "35100.00",
        "34900.00",
        "35050.00",
        "10.5",
        1625097659999,
        "367500.0",
        100,
        "5.2",
        "150.0",
        "0",
    ]

    candle = provider._map_candle(raw_kline)

    assert isinstance(candle, IngestionCandle)
    assert candle.timestamp == 1625097600000
    assert candle.open == 35000.0
    assert candle.close == 35050.0
    assert candle.volume == 10.5
