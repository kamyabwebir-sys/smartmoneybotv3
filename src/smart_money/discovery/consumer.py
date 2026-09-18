"""Deterministic Discovery Registry consumer evidence projection.

Slice 1.32 scope:
- read-only evidence projection
- deterministic and replayable shape
- no execution logic
- no risk calculation
- no reporting/UI payload

Slice 1.33 compatibility:
- canonical dictionary alias for governance verifier
- generated_from metadata field for deterministic provenance
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

_SCHEMA_VERSION = "consumer_evidence_projection.v1"
_CONSUMER_VERSION = "slice-1.32"

# Public, immutable boundary contract used by the Slice 1.33 verifier.
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


def _freeze_value(value: Any) -> Any:
    """Convert nested containers into deterministic immutable values."""
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise TypeError("mapping keys must be strings")
        return MappingProxyType(
            {key: _freeze_value(value[key]) for key in sorted(value)}
        )
    if isinstance(value, list | tuple):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, set | frozenset):
        return tuple(_freeze_value(item) for item in sorted(value, key=str))
    if isinstance(value, float):
        raise TypeError("float values are not canonical")
    return value


def _thaw_value(value: Any) -> Any:
    """Convert immutable internal values into plain deterministic Python values."""
    if isinstance(value, Mapping):
        return {str(key): _thaw_value(value[key]) for key in sorted(value.keys(), key=str)}
    if isinstance(value, tuple):
        return [_thaw_value(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class ConsumerEvidenceProjection:
    """Read-only projection emitted by a Discovery Registry consumer.

    This object carries evidence, score breakdown, boundary metadata, and
    deterministic provenance only. It does not decide, promote, trade, size
    positions, calculate risk, or format reporting payloads.
    """

    registry_snapshot_id: str
    registry_entry_id: str
    evidence_refs: tuple[str, ...]
    deterministic_score_breakdown: Mapping[str, Any]
    replay_manifest_ref: str
    boundary_status: Any
    schema_version: str = _SCHEMA_VERSION
    consumer_version: str = _CONSUMER_VERSION
    generated_from: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        for name in ("registry_snapshot_id", "registry_entry_id", "replay_manifest_ref", "schema_version", "consumer_version"):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(f"{name} must be a string")
            if not value.strip():
                raise ValueError(f"{name} must be non-empty")
            object.__setattr__(self, name, value.strip())
        if not isinstance(self.evidence_refs, tuple):
            raise TypeError("evidence_refs must be a tuple")
        if not all(isinstance(ref, str) and ref.strip() for ref in self.evidence_refs):
            raise ValueError("evidence_refs must contain non-empty strings")
        refs = tuple(sorted(ref.strip() for ref in self.evidence_refs))
        if len(set(refs)) != len(refs):
            raise ValueError("evidence_refs must be unique")
        object.__setattr__(
            self,
            "evidence_refs",
            refs,
        )
        object.__setattr__(
            self,
            "deterministic_score_breakdown",
            _freeze_value(self.deterministic_score_breakdown),
        )
        object.__setattr__(
            self,
            "boundary_status",
            _freeze_value(self.boundary_status),
        )
        object.__setattr__(
            self,
            "generated_from",
            _freeze_value(self.generated_from or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the Slice 1.32 locked deterministic dictionary shape."""
        return {
            "schema_version": self.schema_version,
            "consumer_version": self.consumer_version,
            "registry_snapshot_id": self.registry_snapshot_id,
            "registry_entry_id": self.registry_entry_id,
            "evidence_refs": list(self.evidence_refs),
            "deterministic_score_breakdown": _thaw_value(
                self.deterministic_score_breakdown
            ),
            "replay_manifest_ref": self.replay_manifest_ref,
            "boundary_status": _thaw_value(self.boundary_status),
        }

    def to_canonical_dict(self) -> dict[str, Any]:
        """Return the Slice 1.33 verifier-facing canonical dictionary shape."""
        data = self.to_dict()
        data["generated_from"] = _thaw_value(self.generated_from)
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
        """Build a projection from already-discovered registry evidence."""
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
