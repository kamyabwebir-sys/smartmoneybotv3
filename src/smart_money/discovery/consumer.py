"""Deterministic read-only Discovery Registry evidence projection."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from smart_money.core.frozen import deep_freeze, deep_thaw

_SCHEMA_VERSION = "consumer_evidence_projection.v1"
_CONSUMER_VERSION = "slice-1.32"

FORBIDDEN_OUTPUT_FIELDS = frozenset(
    {
        "trade_execution_instruction",
        "order_intent",
        "position_sizing",
        "stop_loss",
        "take_profit",
        "risk_score_decision",
        "opaque_ml_decision",
        "reporting_payload",
        "promotion_verdict",
    }
)


def _require_non_empty_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _normalize_evidence_refs(value: object) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)):
        raise TypeError("evidence_refs must be a tuple or list")
    normalized = tuple(
        _require_non_empty_text(reference, "evidence_refs") for reference in value
    )
    if len(set(normalized)) != len(normalized):
        raise ValueError("evidence_refs must not contain duplicates")
    return tuple(sorted(normalized))


@dataclass(frozen=True, slots=True)
class ConsumerEvidenceProjection:
    """Evidence-only projection with immutable deterministic provenance."""

    registry_snapshot_id: str
    registry_entry_id: str
    evidence_refs: tuple[str, ...]
    deterministic_score_breakdown: Mapping[str, Any]
    replay_manifest_ref: str
    boundary_status: Mapping[str, Any] | str
    schema_version: str = _SCHEMA_VERSION
    consumer_version: str = _CONSUMER_VERSION
    generated_from: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "registry_snapshot_id",
            _require_non_empty_text(
                self.registry_snapshot_id,
                "registry_snapshot_id",
            ),
        )
        object.__setattr__(
            self,
            "registry_entry_id",
            _require_non_empty_text(self.registry_entry_id, "registry_entry_id"),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_evidence_refs(self.evidence_refs),
        )
        object.__setattr__(
            self,
            "replay_manifest_ref",
            _require_non_empty_text(self.replay_manifest_ref, "replay_manifest_ref"),
        )
        object.__setattr__(
            self,
            "schema_version",
            _require_non_empty_text(self.schema_version, "schema_version"),
        )
        object.__setattr__(
            self,
            "consumer_version",
            _require_non_empty_text(self.consumer_version, "consumer_version"),
        )

        if not isinstance(self.deterministic_score_breakdown, Mapping):
            raise TypeError("deterministic_score_breakdown must be a mapping")
        if not isinstance(self.boundary_status, (Mapping, str)):
            raise TypeError("boundary_status must be a mapping or string")
        if self.generated_from is not None and not isinstance(
            self.generated_from,
            Mapping,
        ):
            raise TypeError("generated_from must be a mapping or None")

        object.__setattr__(
            self,
            "deterministic_score_breakdown",
            deep_freeze(
                self.deterministic_score_breakdown,
                "deterministic_score_breakdown",
            ),
        )
        object.__setattr__(
            self,
            "boundary_status",
            deep_freeze(self.boundary_status, "boundary_status"),
        )
        object.__setattr__(
            self,
            "generated_from",
            deep_freeze(self.generated_from or {}, "generated_from"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the locked Slice 1.32 projection without provenance extension."""
        return {
            "schema_version": self.schema_version,
            "consumer_version": self.consumer_version,
            "registry_snapshot_id": self.registry_snapshot_id,
            "registry_entry_id": self.registry_entry_id,
            "evidence_refs": list(self.evidence_refs),
            "deterministic_score_breakdown": deep_thaw(
                self.deterministic_score_breakdown
            ),
            "replay_manifest_ref": self.replay_manifest_ref,
            "boundary_status": deep_thaw(self.boundary_status),
        }

    def to_canonical_dict(self) -> dict[str, Any]:
        """Return the Slice 1.33 verifier shape with deterministic provenance."""
        data = self.to_dict()
        data["generated_from"] = deep_thaw(self.generated_from)
        return data

    @classmethod
    def from_registry_entry(
        cls,
        *,
        registry_snapshot_id: str,
        registry_entry_id: str,
        evidence_refs: tuple[str, ...] | list[str],
        deterministic_score_breakdown: Mapping[str, Any],
        replay_manifest_ref: str,
        boundary_status: Mapping[str, Any] | str | None = None,
        generated_from: Mapping[str, Any] | None = None,
    ) -> ConsumerEvidenceProjection:
        return cls(
            registry_snapshot_id=registry_snapshot_id,
            registry_entry_id=registry_entry_id,
            evidence_refs=tuple(evidence_refs),
            deterministic_score_breakdown=deterministic_score_breakdown,
            replay_manifest_ref=replay_manifest_ref,
            boundary_status=boundary_status
            or {
                "execution_logic": "absent",
                "risk_calculation": "absent",
                "opaque_ml_decisioning": "absent",
                "reporting_payload": "absent",
                "direct_promotion_verdict": "absent",
            },
            generated_from=generated_from or {"source": "registry_entry"},
        )
