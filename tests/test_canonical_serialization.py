from __future__ import annotations

from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest

from smart_money.core.serialization import canonical_json


def test_dict_key_order_is_stable() -> None:
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'


def test_decimal_serializes_as_string() -> None:
    assert canonical_json({"price": Decimal("100.00")}) == '{"price":"100"}'


def test_datetime_serializes_as_canonical_utc_string() -> None:
    value = datetime(2024, 1, 1, 3, 30, tzinfo=timezone(timedelta(hours=3, minutes=30)))

    assert canonical_json({"time": value}) == '{"time":"2024-01-01T00:00:00Z"}'


def test_naive_datetime_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        canonical_json({"time": datetime(2024, 1, 1, 0, 0)})


def test_nested_structures_serialize_stably() -> None:
    first = {
        "z": (Decimal("2.0"), {"b": Decimal("3.00"), "a": "x"}),
        "a": [1, None, True],
    }
    second = {
        "a": [1, None, True],
        "z": (Decimal("2.00"), {"a": "x", "b": Decimal("3.0")}),
    }

    assert canonical_json(first) == canonical_json(second)
    assert canonical_json(first) == '{"a":[1,null,true],"z":["2",{"a":"x","b":"3"}]}'
