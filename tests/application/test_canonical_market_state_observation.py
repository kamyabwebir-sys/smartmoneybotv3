from dataclasses import FrozenInstanceError

import pytest

from smart_money.application.canonical_market_state_observation import (
    CanonicalMarketStateObservation,
)
from smart_money.ingestion.contracts import EvidencePayload
from tests.application.test_market_state_observation_consumer import _change


def test_typed_observation_round_trips_canonical_payload() -> None:
    change = _change()
    projected = CanonicalMarketStateObservation.from_change(change)
    parsed = CanonicalMarketStateObservation.from_payload(projected.payload)

    assert parsed == projected
    assert parsed.event_id == change.event_id
    assert parsed.source_event_id == change.source_event_id
    assert parsed.market_id == change.market.canonical_id
    assert not hasattr(parsed, "__dict__")
    with pytest.raises(FrozenInstanceError):
        parsed.event_id = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("evidence_type", "generic", "evidence_type"),
        (
            "metadata",
            {
                "authority": "DOMAIN_TRUTH",
                "classification": "OBSERVATION",
                "verification_status": "CANONICAL_SOURCE_EVENT",
                "provenance": {},
            },
            "authority",
        ),
    ],
)
def test_parser_fails_closed_on_schema_or_authority_drift(
    field: str,
    value: object,
    message: str,
) -> None:
    original = CanonicalMarketStateObservation.from_change(_change()).payload
    values = {
        "source_id": original.source_id,
        "evidence_type": original.evidence_type,
        "timestamp": original.timestamp,
        "data": original.data,
        "metadata": original.metadata,
    }
    if field == "metadata":
        value = {**original.metadata, "authority": "DOMAIN_TRUTH"}
    values[field] = value
    payload = EvidencePayload(**values)

    with pytest.raises(ValueError, match=message):
        CanonicalMarketStateObservation.from_payload(payload)
