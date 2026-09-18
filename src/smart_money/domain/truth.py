from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

_SCHEMA_VERSION = "truth_classification.v1"


class TruthLayer(str, Enum):
    OBSERVATION = "OBSERVATION"
    EVIDENCE = "EVIDENCE"
    INFERENCE = "INFERENCE"
    GATE_RESULT = "GATE_RESULT"


class SourceAuthority(str, Enum):
    NONE = "NONE"
    CANONICAL_SOURCE = "CANONICAL_SOURCE"
    EXTERNAL_NON_AUTHORITATIVE = "EXTERNAL_NON_AUTHORITATIVE"
    HUMAN_REVIEWED = "HUMAN_REVIEWED"


class TruthVerificationStatus(str, Enum):
    CANONICAL_SOURCE_EVENT = "CANONICAL_SOURCE_EVENT"
    PROVISIONAL = "PROVISIONAL"
    CONFIRMED = "CONFIRMED"
    INFERRED = "INFERRED"
    CONFLICTED = "CONFLICTED"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class TruthClassification:
    """Non-verdict semantic classification for one system output."""

    layer: TruthLayer
    authority: SourceAuthority
    verification_status: TruthVerificationStatus
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.layer, TruthLayer):
            raise TypeError("layer must be a TruthLayer")
        if not isinstance(self.authority, SourceAuthority):
            raise TypeError("authority must be a SourceAuthority")
        if not isinstance(
            self.verification_status,
            TruthVerificationStatus,
        ):
            raise TypeError(
                "verification_status must be a TruthVerificationStatus"
            )
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported truth classification schema_version")

    @classmethod
    def canonical_observation(cls) -> TruthClassification:
        return cls(
            layer=TruthLayer.OBSERVATION,
            authority=SourceAuthority.NONE,
            verification_status=(
                TruthVerificationStatus.CANONICAL_SOURCE_EVENT
            ),
        )

    def metadata_fields(self) -> dict[str, str]:
        """Return compatibility-preserving EvidencePayload metadata fields."""
        return {
            "authority": self.authority.value,
            "classification": self.layer.value,
            "verification_status": self.verification_status.value,
        }

    def canonical_dict(self) -> dict[str, str]:
        return {
            **self.metadata_fields(),
            "schema_version": self.schema_version,
        }


__all__ = [
    "SourceAuthority",
    "TruthClassification",
    "TruthLayer",
    "TruthVerificationStatus",
]
