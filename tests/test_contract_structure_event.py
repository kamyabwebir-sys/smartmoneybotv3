from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from smart_money.core.contracts import StructureEvent


def _valid_event(evidence_ids: tuple[str, ...] = ("ev_b", "ev_a")) -> StructureEvent:
    return StructureEvent(
        event_type="placeholder_structure_event",
        symbol="SOLUSDT",
        timeframe="1m",
        event_time=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
        price=Decimal("101.00"),
        direction="bullish",
        source_candle_id="candle_abc",
        evidence_ids=evidence_ids,
        rule_id="rule.placeholder",
        rule_version="v1",
    )


def test_valid_event_can_be_created() -> None:
    event = _valid_event()
    assert event.event_type == "placeholder_structure_event"


def test_event_is_immutable() -> None:
    event = _valid_event()
    with pytest.raises(FrozenInstanceError):
        event.direction = "bearish"  # type: ignore[misc]


def test_naive_event_time_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        StructureEvent(
            event_type="placeholder",
            symbol="SOLUSDT",
            timeframe="1m",
            event_time=datetime(2024, 1, 1, 0, 1),
            price=Decimal("101"),
            direction="bullish",
            source_candle_id="candle_abc",
            evidence_ids=("ev_a",),
            rule_id="rule.placeholder",
            rule_version="v1",
        )


def test_invalid_direction_is_rejected() -> None:
    with pytest.raises(ValueError, match="direction"):
        _valid_event().__class__(
            event_type="placeholder",
            symbol="SOLUSDT",
            timeframe="1m",
            event_time=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
            price=Decimal("101"),
            direction="up",
            source_candle_id="candle_abc",
            evidence_ids=("ev_a",),
            rule_id="rule.placeholder",
            rule_version="v1",
        )


def test_float_price_is_rejected() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        StructureEvent(
            event_type="placeholder",
            symbol="SOLUSDT",
            timeframe="1m",
            event_time=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
            price=101.0,  # type: ignore[arg-type]
            direction="bullish",
            source_candle_id="candle_abc",
            evidence_ids=("ev_a",),
            rule_id="rule.placeholder",
            rule_version="v1",
        )


def test_evidence_ids_list_is_rejected() -> None:
    with pytest.raises(TypeError, match="tuple"):
        StructureEvent(
            event_type="placeholder",
            symbol="SOLUSDT",
            timeframe="1m",
            event_time=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
            price=Decimal("101"),
            direction="bullish",
            source_candle_id="candle_abc",
            evidence_ids=["ev_a"],  # type: ignore[arg-type]
            rule_id="rule.placeholder",
            rule_version="v1",
        )


def test_empty_evidence_id_is_rejected() -> None:
    with pytest.raises(ValueError, match="evidence_ids"):
        _valid_event(evidence_ids=("ev_a", " "))


def test_evidence_ids_are_canonically_sorted() -> None:
    assert _valid_event().evidence_ids == ("ev_a", "ev_b")


def test_deterministic_id_is_stable_when_evidence_order_differs() -> None:
    first = _valid_event(evidence_ids=("ev_b", "ev_a"))
    second = _valid_event(evidence_ids=("ev_a", "ev_b"))

    assert first.deterministic_id() == second.deterministic_id()
