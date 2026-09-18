from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, settings, strategies as st

from smart_money.core.ids import deterministic_id
from smart_money.core.serialization import canonical_json


text = st.text(min_size=1, max_size=24).filter(lambda value: bool(value.strip()))
scalars = st.one_of(st.none(), st.booleans(), st.integers(), text, st.decimals(allow_nan=False, allow_infinity=False))
payloads = st.dictionaries(text, scalars, max_size=12)


@settings(max_examples=250, deadline=None)
@given(payloads)
def test_mapping_order_never_changes_canonical_identity(payload: dict[str, object]) -> None:
    reversed_payload = dict(reversed(tuple(payload.items())))
    assert canonical_json(payload) == canonical_json(reversed_payload)
    assert deterministic_id("fuzz", payload) == deterministic_id("fuzz", reversed_payload)


@settings(max_examples=150, deadline=None)
@given(st.lists(scalars, max_size=16))
def test_tuple_and_list_have_same_canonical_form(values: list[object]) -> None:
    assert canonical_json(values) == canonical_json(tuple(values))


@given(st.floats(allow_nan=True, allow_infinity=True))
def test_binary_float_is_always_rejected(value: float) -> None:
    with pytest.raises(TypeError, match="float values are not allowed"):
        canonical_json({"value": value})


@given(st.decimals(allow_nan=False, allow_infinity=False))
def test_decimal_canonicalization_is_idempotent(value: Decimal) -> None:
    encoded = canonical_json({"value": value})
    assert encoded == canonical_json({"value": value})
