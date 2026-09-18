"""Behavioral contracts for Candle and StructureEvent domain objects.

Shared invariants tested once via parametrize; object-specific behaviors tested
in dedicated sections.  Replaces test_contract_candle.py and
test_contract_structure_event.py.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from smart_money.core.contracts import Candle, StructureEvent


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _make_candle(**overrides) -> Candle:
    defaults = dict(
        symbol="SOLUSDT",
        timeframe="1m",
        open_time=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
        close_time=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
        open=Decimal("100"),
        high=Decimal("105"),
        low=Decimal("99"),
        close=Decimal("101"),
        volume=Decimal("1000"),
        source="fixture",
    )
    defaults.update(overrides)
    return Candle(**defaults)


def _make_event(**overrides) -> StructureEvent:
    defaults = dict(
        event_type="placeholder",
        symbol="SOLUSDT",
        timeframe="1m",
        event_time=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
        price=Decimal("101"),
        direction="bullish",
        source_candle_id="candle_abc",
        evidence_ids=("ev_b", "ev_a"),
        rule_id="rule.placeholder",
        rule_version="v1",
    )
    defaults.update(overrides)
    return StructureEvent(**defaults)


# ── Shared invariants (both Candle and StructureEvent) ────────────────────────

_SHARED_CASES = [
    pytest.param(_make_candle, "Candle", id="Candle"),
    pytest.param(_make_event, "StructureEvent", id="StructureEvent"),
]


@pytest.mark.parametrize("factory,name", _SHARED_CASES)
def test_valid_object_is_created(factory, name: str) -> None:
    obj = factory()
    assert obj is not None


@pytest.mark.parametrize("factory,name", _SHARED_CASES)
def test_object_is_frozen(factory, name: str) -> None:
    obj = factory()
    with pytest.raises(FrozenInstanceError):
        obj.symbol = "NOPE"  # type: ignore[misc]


@pytest.mark.parametrize("factory,name", _SHARED_CASES)
def test_deterministic_id_is_stable(factory, name: str) -> None:
    assert factory().deterministic_id() == factory().deterministic_id()


# ── Candle-specific behavior ─────────────────────────────────────────────────

class TestCandle:
    def test_schema_version_default(self) -> None:
        assert _make_candle().schema_version == "candle.v1"

    def test_canonical_dict_keys(self) -> None:
        expected = [
            "schema_version", "symbol", "timeframe", "open_time", "close_time",
            "open", "high", "low", "close", "volume", "source",
        ]
        assert list(_make_candle().canonical_dict().keys()) == expected

    @pytest.mark.parametrize("bad_price", ["open", "high", "low", "close"])
    def test_float_price_is_rejected(self, bad_price: str) -> None:
        with pytest.raises(TypeError, match="Decimal"):
            _make_candle(**{bad_price: 100.0})  # type: ignore[arg-type]

    def test_negative_volume_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="volume"):
            _make_candle(volume=Decimal("-1"))

    def test_open_time_must_precede_close_time(self) -> None:
        ts = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="open_time"):
            _make_candle(open_time=ts, close_time=ts)

    def test_naive_datetime_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="timezone-aware"):
            _make_candle(open_time=datetime(2024, 1, 1, 0, 0))

    def test_high_must_be_greatest(self) -> None:
        with pytest.raises(ValueError, match="high"):
            _make_candle(high=Decimal("98"))  # below low=99


# ── StructureEvent-specific behavior ─────────────────────────────────────────

class TestStructureEvent:
    def test_evidence_ids_are_sorted(self) -> None:
        assert _make_event().evidence_ids == ("ev_a", "ev_b")

    def test_order_of_evidence_does_not_change_id(self) -> None:
        a = _make_event(evidence_ids=("ev_b", "ev_a"))
        b = _make_event(evidence_ids=("ev_a", "ev_b"))
        assert a.deterministic_id() == b.deterministic_id()

    def test_invalid_direction_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="direction"):
            _make_event(direction="up")

    def test_float_price_is_rejected(self) -> None:
        with pytest.raises(TypeError, match="Decimal"):
            _make_event(price=101.0)  # type: ignore[arg-type]

    def test_list_evidence_is_rejected(self) -> None:
        with pytest.raises(TypeError, match="tuple"):
            _make_event(evidence_ids=["ev_a"])  # type: ignore[arg-type]

    def test_empty_evidence_id_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="evidence_ids"):
            _make_event(evidence_ids=("ev_a", " "))

    def test_naive_event_time_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="timezone-aware"):
            _make_event(event_time=datetime(2024, 1, 1, 0, 1))
