from decimal import Decimal

import pytest

from smart_money.adapters.worldmonitor_macro import WorldMonitorMacroAdapter
from smart_money.domain.macro_context import MacroObservationStatus


def _payload(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "metric": "risk_sentiment",
        "observed_at": 1_700_000_000,
        "value": "0.25",
        "unit": "index",
        "status": "provisional",
        "source_revision": "r1",
    }
    value.update(overrides)
    return value


def test_adapter_projects_fixture_to_canonical_observation() -> None:
    observation = WorldMonitorMacroAdapter.from_payload(_payload())

    assert observation.source_id == "worldmonitor"
    assert observation.value == Decimal("0.25")
    assert observation.status is MacroObservationStatus.PROVISIONAL
    assert observation.canonical_id == (
        WorldMonitorMacroAdapter.from_payload(_payload()).canonical_id
    )


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("observed_at", True, "observed_at"),
        ("value", "NaN", "finite"),
        ("status", "BUY", "status"),
        ("source_revision", "", "source_revision"),
    ],
)
def test_adapter_fails_closed_on_invalid_fixture(
    field: str,
    value: object,
    error: str,
) -> None:
    with pytest.raises((TypeError, ValueError), match=error):
        WorldMonitorMacroAdapter.from_payload(_payload(**{field: value}))


def test_adapter_rejects_schema_drift() -> None:
    with pytest.raises(ValueError, match="keys"):
        WorldMonitorMacroAdapter.from_payload(
            _payload(unexpected="ignored")
        )
