from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from smart_money.domain.macro_context import (
    MacroEvidenceObservation,
    MacroObservationStatus,
)


def _observation(**overrides: object) -> MacroEvidenceObservation:
    values: dict[str, object] = {
        "source_id": "worldmonitor",
        "metric": "risk_sentiment",
        "observed_at": 1_700_000_000,
        "value": Decimal("0.25"),
        "unit": "index",
        "status": MacroObservationStatus.PROVISIONAL,
        "source_revision": "r1",
    }
    values.update(overrides)
    return MacroEvidenceObservation(**values)


def test_macro_observation_is_immutable_and_content_addressed() -> None:
    observation = _observation()

    assert observation.canonical_id.startswith("macro_evidence_observation_")
    assert observation.canonical_dict()["status"] is (
        MacroObservationStatus.PROVISIONAL
    )
    assert not hasattr(observation, "__dict__")
    with pytest.raises(FrozenInstanceError):
        observation.metric = "other"  # type: ignore[misc]


def test_macro_observation_id_changes_with_revision_or_value() -> None:
    assert _observation().canonical_id != _observation(source_revision="r2").canonical_id
    assert _observation().canonical_id != _observation(value=Decimal("0.26")).canonical_id


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("observed_at", -1, "non-negative"),
        ("value", 0.25, "Decimal"),
        ("status", "PROVISIONAL", "MacroObservationStatus"),
        ("metric", " ", "non-empty"),
    ],
)
def test_macro_observation_fails_closed(field: str, value: object, error: str) -> None:
    with pytest.raises((TypeError, ValueError), match=error):
        _observation(**{field: value})
