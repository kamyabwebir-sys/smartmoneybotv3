from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any

from smart_money.core.ids import deterministic_id


class MacroObservationStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    PROVISIONAL = "PROVISIONAL"
    CONFLICTED = "CONFLICTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class MacroEvidenceObservation:
    """Immutable, non-authoritative macro observation for analytics context."""

    source_id: str
    metric: str
    observed_at: int
    value: Decimal
    unit: str
    status: MacroObservationStatus = MacroObservationStatus.UNKNOWN
    source_revision: str = ""
    schema_version: str = "macro_evidence_observation.v1"

    def __post_init__(self) -> None:
        for field_name in ("source_id", "metric", "unit"):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string")
            normalized = value.strip()
            if not normalized:
                raise ValueError(f"{field_name} must be non-empty")
            object.__setattr__(self, field_name, normalized)
        if isinstance(self.observed_at, bool) or not isinstance(
            self.observed_at, int
        ):
            raise TypeError("observed_at must be an integer")
        if self.observed_at < 0:
            raise ValueError("observed_at must be non-negative")
        if not isinstance(self.value, Decimal):
            raise TypeError("value must be Decimal")
        if not self.value.is_finite():
            raise ValueError("value must be finite")
        if not isinstance(self.status, MacroObservationStatus):
            raise TypeError("status must be a MacroObservationStatus")
        if not isinstance(self.source_revision, str):
            raise TypeError("source_revision must be a string")
        if self.schema_version != "macro_evidence_observation.v1":
            raise ValueError("unsupported MacroEvidenceObservation schema_version")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "observed_at": self.observed_at,
            "schema_version": self.schema_version,
            "source_id": self.source_id,
            "source_revision": self.source_revision,
            "status": self.status,
            "unit": self.unit,
            "value": self.value,
        }

    @property
    def canonical_id(self) -> str:
        return deterministic_id("macro_evidence_observation", self.canonical_dict())


__all__ = ["MacroEvidenceObservation", "MacroObservationStatus"]
