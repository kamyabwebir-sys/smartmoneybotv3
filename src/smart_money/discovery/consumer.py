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

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


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
        return MappingProxyType(
            {str(key): _freeze_value(value[key]) for key in sorted(value.keys(), key=str)}
        )
    if isinstance(value, list | tuple):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, set | frozenset):
        return tuple(_freeze_value(item) for item in sorted(value, key=str))
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
        object.__setattr__(self, "registry_snapshot_id", str(self.registry_snapshot_id))
        object.__setattr__(self, "registry_entry_id", str(self.registry_entry_id))
        object.__setattr__(
            self,
            "evidence_refs",
            tuple(str(ref) for ref in self.evidence_refs),
        )
        object.__setattr__(
            self,
            "deterministic_score_breakdown",
            _freeze_value(self.deterministic_score_breakdown),
        )
        object.__setattr__(self, "replay_manifest_ref", str(self.replay_manifest_ref))
        object.__setattr__(
            self,
            "boundary_status",
            _freeze_value(self.boundary_status),
        )
        object.__setattr__(self, "schema_version", str(self.schema_version))
        object.__setattr__(self, "consumer_version", str(self.consumer_version))
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
    ) -> "ConsumerEvidenceProjection":
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

