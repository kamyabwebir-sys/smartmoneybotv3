from dataclasses import FrozenInstanceError
from datetime import datetime
from decimal import Decimal

import pytest

from smart_money.ingestion.contracts import IngestionCandle


def test_ingestion_candle_is_immutable():
    candle = IngestionCandle(
        symbol="SOL/USDC",
        timestamp=datetime.now(),
        open=Decimal("100"),
        high=Decimal("110"),
        low=Decimal("90"),
        close=Decimal("105"),
        volume=Decimal("1000"),
        interval="1m",
        source_id="provider_a",
    )

    with pytest.raises(FrozenInstanceError):
        candle.close = Decimal("120")  # type: ignore


def test_ingestion_candle_types():
    candle = IngestionCandle(
        symbol="BTC/USDC",
        timestamp=datetime.now(),
        open=Decimal("50000"),
        high=Decimal("51000"),
        low=Decimal("49000"),
        close=Decimal("50500"),
        volume=Decimal("10"),
        interval="1h",
        source_id="binance",
    )
    assert isinstance(candle.open, Decimal)
    assert candle.is_final is True
