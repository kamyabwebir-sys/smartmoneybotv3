from dataclasses import FrozenInstanceError

import pytest

from smart_money.core.events import DomainEventEnvelope


def test_valid_envelope_creation() -> None:
    envelope = DomainEventEnvelope(
        event_id="evt-001",
        event_type="structure.detected",
        occurred_at="2026-07-16T00:00:00Z",
        payload={"symbol": "SOL"},
        metadata={"source": "test"},
    )

    assert envelope.event_id == "evt-001"
    assert envelope.event_type == "structure.detected"
    assert envelope.occurred_at == "2026-07-16T00:00:00Z"


@pytest.mark.parametrize("field_name", ["event_id", "event_type", "occurred_at"])
@pytest.mark.parametrize("bad_value", ["", "   ", 123, None])
def test_rejects_invalid_required_string_fields(field_name: str, bad_value: object) -> None:
    values = {
        "event_id": "evt-001",
        "event_type": "structure.detected",
        "occurred_at": "2026-07-16T00:00:00Z",
    }
    values[field_name] = bad_value

    with pytest.raises(ValueError):
        DomainEventEnvelope(**values)


def test_defaults_payload_and_metadata_to_empty_mappings() -> None:
    envelope = DomainEventEnvelope(
        event_id="evt-001",
        event_type="structure.detected",
        occurred_at="2026-07-16T00:00:00Z",
    )

    assert dict(envelope.payload) == {}
    assert dict(envelope.metadata) == {}


def test_payload_and_metadata_are_defensively_copied() -> None:
    payload = {"symbol": "SOL"}
    metadata = {"source": "test"}

    envelope = DomainEventEnvelope(
        event_id="evt-001",
        event_type="structure.detected",
        occurred_at="2026-07-16T00:00:00Z",
        payload=payload,
        metadata=metadata,
    )

    payload["symbol"] = "ETH"
    metadata["source"] = "mutated"

    assert dict(envelope.payload) == {"symbol": "SOL"}
    assert dict(envelope.metadata) == {"source": "test"}


def test_payload_and_metadata_are_shallowly_immutable() -> None:
    envelope = DomainEventEnvelope(
        event_id="evt-001",
        event_type="structure.detected",
        occurred_at="2026-07-16T00:00:00Z",
        payload={"symbol": "SOL"},
        metadata={"source": "test"},
    )

    with pytest.raises(TypeError):
        envelope.payload["symbol"] = "ETH"

    with pytest.raises(TypeError):
        envelope.metadata["source"] = "mutated"


def test_envelope_is_immutable() -> None:
    envelope = DomainEventEnvelope(
        event_id="evt-001",
        event_type="structure.detected",
        occurred_at="2026-07-16T00:00:00Z",
    )

    with pytest.raises(FrozenInstanceError):
        envelope.event_id = "evt-002"


def test_to_dict_returns_plain_deterministic_dict() -> None:
    envelope = DomainEventEnvelope(
        event_id="evt-001",
        event_type="structure.detected",
        occurred_at="2026-07-16T00:00:00Z",
        payload={"symbol": "SOL"},
        metadata={"source": "test"},
    )

    assert envelope.to_dict() == {
        "event_id": "evt-001",
        "event_type": "structure.detected",
        "occurred_at": "2026-07-16T00:00:00Z",
        "payload": {"symbol": "SOL"},
        "metadata": {"source": "test"},
    }
    assert type(envelope.to_dict()["payload"]) is dict
    assert type(envelope.to_dict()["metadata"]) is dict
