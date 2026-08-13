from __future__ import annotations

from types import MappingProxyType

import pytest

from smart_money.ingestion.envelope import IngestionEnvelope, IngestionEnvelopeError


def test_envelope_is_deterministic_and_deep_frozen():
    payload = {"b": [2, {"x": "y"}], "a": 1}
    metadata = {"origin": "unit-test"}

    envelope = IngestionEnvelope(
        source="feed",
        symbol="SOL",
        payload=payload,
        metadata=metadata,
    )
    first_id = envelope.deterministic_id()
    first_canonical = envelope.canonical_dict()

    payload["b"][1]["x"] = "changed"
    metadata["origin"] = "changed"

    assert envelope.payload["b"][1]["x"] == "y"
    assert envelope.metadata["origin"] == "unit-test"
    assert envelope.deterministic_id() == first_id
    assert envelope.canonical_dict() == first_canonical
    assert isinstance(envelope.payload, MappingProxyType)
    assert isinstance(envelope.metadata, MappingProxyType)


def test_envelope_canonical_dict_sorts_nested_mapping_keys():
    first = IngestionEnvelope(
        source="feed",
        symbol="SOL",
        payload={"z": 1, "a": {"b": 2, "a": 1}},
        metadata={"m": [2, 1]},
    )
    second = IngestionEnvelope(
        source="feed",
        symbol="SOL",
        payload={"a": {"a": 1, "b": 2}, "z": 1},
        metadata={"m": [2, 1]},
    )

    assert first.canonical_dict() == second.canonical_dict()
    assert first.deterministic_id() == second.deterministic_id()


@pytest.mark.parametrize(
    ("field_name", "value", "error"),
    [
        ("source", "", "source must be non-empty"),
        ("source", 1, "source must be a string"),
        ("symbol", "", "symbol must be non-empty"),
        ("symbol", None, "symbol must be a string"),
        ("payload", [], "payload must be a mapping"),
        ("metadata", None, "metadata must be a mapping"),
    ],
)
def test_envelope_rejects_invalid_boundary_values(field_name, value, error):
    kwargs = {
        "source": "feed",
        "symbol": "SOL",
        "payload": {},
        "metadata": {},
    }
    kwargs[field_name] = value

    with pytest.raises(IngestionEnvelopeError, match=error):
        IngestionEnvelope(**kwargs)


def test_envelope_rejects_unsupported_payload_value_type():
    with pytest.raises(IngestionEnvelopeError, match="unsupported value type"):
        IngestionEnvelope(
            source="feed", symbol="SOL", payload={"bad": object()}, metadata={}
        )


def test_envelope_rejects_non_string_mapping_keys():
    with pytest.raises(IngestionEnvelopeError, match="payload keys must be strings"):
        IngestionEnvelope(source="feed", symbol="SOL", payload={1: "bad"}, metadata={})


def test_envelope_rejects_mixed_mapping_key_types_deterministically():
    with pytest.raises(IngestionEnvelopeError, match="payload keys must be strings"):
        IngestionEnvelope(
            source="feed",
            symbol="SOL",
            payload={"valid": 1, 2: "bad"},
            metadata={},
        )


def test_envelope_rejects_duplicate_normalized_keys():
    with pytest.raises(
        IngestionEnvelopeError,
        match="payload contains duplicate normalized keys",
    ):
        IngestionEnvelope(
            source="feed",
            symbol="SOL",
            payload={" key": 1, "key": 2},
            metadata={},
        )
