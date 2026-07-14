from __future__ import annotations

from decimal import Decimal

import pytest

from smart_money.core.ids import deterministic_id


def test_same_payload_produces_same_id() -> None:
    payload = {"symbol": "SOLUSDT", "price": Decimal("100.0")}
    assert deterministic_id("candle", payload) == deterministic_id("candle", payload)


def test_different_payload_produces_different_id() -> None:
    first = deterministic_id("candle", {"symbol": "SOLUSDT"})
    second = deterministic_id("candle", {"symbol": "BTCUSDT"})

    assert first != second


def test_key_order_does_not_affect_id() -> None:
    first = deterministic_id("candle", {"a": 1, "b": 2})
    second = deterministic_id("candle", {"b": 2, "a": 1})

    assert first == second


def test_namespace_affects_id() -> None:
    payload = {"a": 1}

    assert deterministic_id("candle", payload) != deterministic_id("structure_event", payload)


def test_float_values_are_rejected() -> None:
    with pytest.raises(TypeError, match="float"):
        deterministic_id("candle", {"price": 1.23})
