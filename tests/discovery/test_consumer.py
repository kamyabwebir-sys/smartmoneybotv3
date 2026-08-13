from __future__ import annotations

from decimal import Decimal
from types import MappingProxyType

import pytest

from smart_money.discovery.consumer import ConsumerEvidenceProjection


def _projection(**overrides: object) -> ConsumerEvidenceProjection:
    values = {
        "registry_snapshot_id": "snapshot-1",
        "registry_entry_id": "entry-1",
        "evidence_refs": ("evidence-b", "evidence-a"),
        "deterministic_score_breakdown": {
            "structure": Decimal("0.5"),
            "details": {"confirmed": True},
        },
        "replay_manifest_ref": "manifest-1",
        "boundary_status": {"execution_logic": "absent"},
        "generated_from": {"source": "registry_entry"},
    }
    values.update(overrides)
    return ConsumerEvidenceProjection(**values)


def test_projection_is_deeply_immutable_and_deterministic() -> None:
    score = {"details": {"confirmed": True}, "structure": Decimal("0.5")}
    projection = _projection(deterministic_score_breakdown=score)
    score["details"]["confirmed"] = False

    assert projection.evidence_refs == ("evidence-a", "evidence-b")
    assert projection.deterministic_score_breakdown["details"]["confirmed"] is True
    assert isinstance(projection.deterministic_score_breakdown, MappingProxyType)
    assert projection.to_canonical_dict()["generated_from"] == {
        "source": "registry_entry"
    }
    assert "generated_from" not in projection.to_dict()


@pytest.mark.parametrize(
    ("field_name", "value", "error_type"),
    [
        ("registry_snapshot_id", "", ValueError),
        ("registry_entry_id", None, TypeError),
        ("evidence_refs", ("",), ValueError),
        ("evidence_refs", ("same", "same"), ValueError),
        ("replay_manifest_ref", "", ValueError),
        ("schema_version", "", ValueError),
        ("consumer_version", 1, TypeError),
    ],
)
def test_projection_rejects_invalid_identity_fields(
    field_name: str,
    value: object,
    error_type: type[Exception],
) -> None:
    with pytest.raises(error_type):
        _projection(**{field_name: value})


def test_projection_rejects_non_string_mapping_keys_and_float_scores() -> None:
    with pytest.raises(TypeError, match="keys must be strings"):
        _projection(deterministic_score_breakdown={1: "collision"})

    with pytest.raises(TypeError, match="float"):
        _projection(deterministic_score_breakdown={"score": 0.5})


def test_factory_preserves_locked_legacy_and_canonical_shapes() -> None:
    projection = ConsumerEvidenceProjection.from_registry_entry(
        registry_snapshot_id="snapshot-1",
        registry_entry_id="entry-1",
        evidence_refs=["evidence-1"],
        deterministic_score_breakdown={"score": Decimal("1")},
        replay_manifest_ref="manifest-1",
    )

    assert "generated_from" not in projection.to_dict()
    assert projection.to_canonical_dict()["generated_from"] == {
        "source": "registry_entry"
    }
