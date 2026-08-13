from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from smart_money.core.contracts import StructureEvent


def _event(**overrides: object) -> StructureEvent:
    kwargs = {
        "schema_version": "structure_event.v1",
        "event_type": "swing_high",
        "symbol": "SOL",
        "timeframe": "1m",
        "event_time": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "price": Decimal("100.25"),
        "direction": "bearish",
        "source_candle_id": "candle:abc",
        "evidence_ids": ("ev_b", "ev_a"),
        "rule_id": "structure.placeholder",
        "rule_version": "v1",
    }
    kwargs.update(overrides)
    return StructureEvent(**kwargs)


def test_structure_event_has_canonical_dict_and_deterministic_id():
    first = _event()
    second = _event(evidence_ids=("ev_a", "ev_b"))

    assert first.canonical_dict() == second.canonical_dict()
    assert first.deterministic_id() == second.deterministic_id()
    assert first.canonical_dict() == {
        "schema_version": "structure_event.v1",
        "event_type": "swing_high",
        "symbol": "SOL",
        "timeframe": "1m",
        "event_time": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "price": Decimal("100.25"),
        "direction": "bearish",
        "source_candle_id": "candle:abc",
        "evidence_ids": ("ev_a", "ev_b"),
        "rule_id": "structure.placeholder",
        "rule_version": "v1",
    }


@pytest.mark.parametrize(
    ("field_name", "value", "error_type"),
    [
        ("event_type", "", ValueError),
        ("symbol", "", ValueError),
        ("timeframe", "", ValueError),
        ("source_candle_id", "", ValueError),
        ("rule_id", "", ValueError),
        ("rule_version", "", ValueError),
        ("price", 100.25, TypeError),
        ("direction", "sideways", ValueError),
        ("evidence_ids", ["ev_a"], TypeError),
        ("evidence_ids", ("ev_a", ""), ValueError),
    ],
)
def test_structure_event_rejects_invalid_values(field_name, value, error_type):
    with pytest.raises(error_type):
        _event(**{field_name: value})


def test_structure_event_rejects_naive_event_time():
    with pytest.raises(ValueError, match="timezone-aware"):
        _event(event_time=datetime(2025, 1, 1))


def test_structure_event_canonicalizes_evidence_ids_order():
    event = _event(evidence_ids=("ev_b", "ev_a"))

    assert event.evidence_ids == ("ev_a", "ev_b")
