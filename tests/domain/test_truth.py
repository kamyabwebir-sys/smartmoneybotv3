from dataclasses import FrozenInstanceError

import pytest

from smart_money.domain.truth import (
    SourceAuthority,
    TruthClassification,
    TruthLayer,
    TruthVerificationStatus,
)


def test_canonical_observation_preserves_existing_metadata_contract() -> None:
    classification = TruthClassification.canonical_observation()

    assert classification.metadata_fields() == {
        "authority": "NONE",
        "classification": "OBSERVATION",
        "verification_status": "CANONICAL_SOURCE_EVENT",
    }
    assert classification.canonical_dict()["schema_version"] == (
        "truth_classification.v1"
    )
    assert not hasattr(classification, "__dict__")
    with pytest.raises(FrozenInstanceError):
        classification.layer = TruthLayer.EVIDENCE  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("layer", "OBSERVATION", "TruthLayer"),
        ("authority", "NONE", "SourceAuthority"),
        (
            "verification_status",
            "CONFIRMED",
            "TruthVerificationStatus",
        ),
    ],
)
def test_truth_classification_rejects_untyped_values(
    field: str,
    value: str,
    message: str,
) -> None:
    values = {
        "layer": TruthLayer.OBSERVATION,
        "authority": SourceAuthority.NONE,
        "verification_status": (
            TruthVerificationStatus.CANONICAL_SOURCE_EVENT
        ),
    }
    values[field] = value

    with pytest.raises(TypeError, match=message):
        TruthClassification(**values)
