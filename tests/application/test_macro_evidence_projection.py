from decimal import Decimal

import pytest

from smart_money.application.macro_evidence_projection import (
    ExternalMacroEvidenceProjection,
)
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


def test_projection_preserves_external_provenance_and_status() -> None:
    projected = ExternalMacroEvidenceProjection.from_observation(_observation())
    payload = projected.payload

    assert payload.evidence_type == "external_macro_observation"
    assert payload.timestamp == 1_700_000_000
    assert payload.metadata["authority"] == "EXTERNAL_NON_AUTHORITATIVE"
    assert payload.metadata["classification"] == "EVIDENCE"
    assert payload.metadata["verification_status"] == "PROVISIONAL"
    assert payload.metadata["provenance"]["source_revision"] == "r1"
    assert payload.data["macro_observation"]["canonical_id"] == (
        projected.observation_id
    )


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (MacroObservationStatus.CONFIRMED, "CONFIRMED"),
        (MacroObservationStatus.CONFLICTED, "CONFLICTED"),
        (MacroObservationStatus.UNKNOWN, "UNKNOWN"),
    ],
)
def test_projection_maps_observation_status(
    status: MacroObservationStatus,
    expected: str,
) -> None:
    projected = ExternalMacroEvidenceProjection.from_observation(
        _observation(status=status)
    )
    assert projected.payload.metadata["verification_status"] == expected


def test_projection_is_deterministic() -> None:
    left = ExternalMacroEvidenceProjection.from_observation(_observation())
    right = ExternalMacroEvidenceProjection.from_observation(_observation())

    assert left.payload.get_canonical_id() == right.payload.get_canonical_id()
    assert left.payload.canonical_dict() == right.payload.canonical_dict()


def test_projection_fails_closed_on_payload_classification_drift() -> None:
    projected = ExternalMacroEvidenceProjection.from_observation(_observation())
    original = projected.payload
    payload = type(original)(
        source_id=original.source_id,
        evidence_type=original.evidence_type,
        timestamp=original.timestamp,
        data=original.data,
        metadata={**original.metadata, "classification": "INFERENCE"},
    )

    with pytest.raises(ValueError, match="classification"):
        ExternalMacroEvidenceProjection(
            payload=payload,
            observation_id=projected.observation_id,
        )
