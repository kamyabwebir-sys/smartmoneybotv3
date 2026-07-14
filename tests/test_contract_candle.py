from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from smart_money.core.contracts import Candle


def _valid_candle() -> Candle:
    return Candle(
        symbol="SOLUSDT",
        timeframe="1m",
        open_time=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
        close_time=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
        open=Decimal("100.00"),
        high=Decimal("105.00"),
        low=Decimal("99.00"),
        close=Decimal("101.00"),
        volume=Decimal("1234.50"),
        source="fixture",
    )


def test_valid_candle_can_be_created() -> None:
    candle = _valid_candle()
    assert candle.symbol == "SOLUSDT"
    assert candle.schema_version == "candle.v1"


def test_candle_is_immutable() -> None:
    candle = _valid_candle()
    with pytest.raises(FrozenInstanceError):
        candle.symbol = "BTCUSDT"  # type: ignore[misc]


def test_naive_datetime_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        Candle(
            symbol="SOLUSDT",
            timeframe="1m",
            open_time=datetime(2024, 1, 1, 0, 0),
            close_time=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
            open=Decimal("100"),
            high=Decimal("101"),
            low=Decimal("99"),
            close=Decimal("100"),
            volume=Decimal("1"),
            source="fixture",
        )


def test_open_time_must_be_before_close_time() -> None:
    timestamp = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="open_time"):
        Candle(
            symbol="SOLUSDT",
            timeframe="1m",
            open_time=timestamp,
            close_time=timestamp,
            open=Decimal("100"),
            high=Decimal("101"),
            low=Decimal("99"),
            close=Decimal("100"),
            volume=Decimal("1"),
            source="fixture",
        )


def test_float_price_is_rejected() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        Candle(
            symbol="SOLUSDT",
            timeframe="1m",
            open_time=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
            close_time=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
            open=100.0,  # type: ignore[arg-type]
            high=Decimal("101"),
            low=Decimal("99"),
            close=Decimal("100"),
            volume=Decimal("1"),
            source="fixture",
        )


def test_invalid_ohlc_relationship_is_rejected() -> None:
    with pytest.raises(ValueError, match="high"):
        Candle(
            symbol="SOLUSDT",
            timeframe="1m",
            open_time=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
            close_time=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
            open=Decimal("100"),
            high=Decimal("99"),
            low=Decimal("98"),
            close=Decimal("100"),
            volume=Decimal("1"),
            source="fixture",
        )


def test_negative_volume_is_rejected() -> None:
    with pytest.raises(ValueError, match="volume"):
        Candle(
            symbol="SOLUSDT",
            timeframe="1m",
            open_time=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
            close_time=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
            open=Decimal("100"),
            high=Decimal("101"),
            low=Decimal("99"),
            close=Decimal("100"),
            volume=Decimal("-1"),
            source="fixture",
        )


def test_canonical_dict_is_stable() -> None:
    candle = _valid_candle()
    assert list(candle.canonical_dict().keys()) == [
        "schema_version",
        "symbol",
        "timeframe",
        "open_time",
        "close_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "source",
    ]


def test_deterministic_id_is_stable_across_equivalent_objects() -> None:
    assert _valid_candle().deterministic_id() == _valid_candle().deterministic_id()
