from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar

from smart_money.domain.macro_context import (
    MacroEvidenceObservation,
    MacroObservationStatus,
)
from smart_money.domain.truth import (
    SourceAuthority,
    TruthClassification,
    TruthLayer,
    TruthVerificationStatus,
)
from smart_money.ingestion.contracts import EvidencePayload

_EVIDENCE_TYPE = "external_macro_observation"


def _status(value: MacroObservationStatus) -> TruthVerificationStatus:
    return TruthVerificationStatus(value.value)


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return value


@dataclass(frozen=True, slots=True)
class ExternalMacroEvidenceProjection:
    """Typed, non-authoritative projection of one macro observation."""

    EVIDENCE_TYPE: ClassVar[str] = _EVIDENCE_TYPE
    payload: EvidencePayload
    observation_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.payload, EvidencePayload):
            raise TypeError("payload must be an EvidencePayload")
        if self.payload.evidence_type != self.EVIDENCE_TYPE:
            raise ValueError("unsupported external macro evidence_type")
        data = _mapping(self.payload.data.get("macro_observation"), "macro_observation")
        provenance = _mapping(self.payload.metadata.get("provenance"), "provenance")
        if set(self.payload.data) != {"macro_observation"}:
            raise ValueError("external macro data keys do not match")
        if set(self.payload.metadata) != {
            "authority",
            "classification",
            "provenance",
            "verification_status",
        }:
            raise ValueError("external macro metadata keys do not match")
        if self.payload.metadata["authority"] != SourceAuthority.EXTERNAL_NON_AUTHORITATIVE.value:
            raise ValueError("external macro authority mismatch")
        if self.payload.metadata["classification"] != TruthLayer.EVIDENCE.value:
            raise ValueError("external macro classification mismatch")
        if data.get("canonical_id") != self.observation_id:
            raise ValueError("external macro observation_id mismatch")
        if provenance.get("source_id") != self.payload.source_id:
            raise ValueError("external macro provenance source mismatch")

    @classmethod
    def from_observation(
        cls,
        observation: MacroEvidenceObservation,
    ) -> ExternalMacroEvidenceProjection:
        if not isinstance(observation, MacroEvidenceObservation):
            raise TypeError("observation must be a MacroEvidenceObservation")
        classification = TruthClassification(
            layer=TruthLayer.EVIDENCE,
            authority=SourceAuthority.EXTERNAL_NON_AUTHORITATIVE,
            verification_status=_status(observation.status),
        )
        data = {
            **observation.canonical_dict(),
            "canonical_id": observation.canonical_id,
        }
        payload = EvidencePayload(
            source_id=observation.source_id,
            evidence_type=cls.EVIDENCE_TYPE,
            timestamp=observation.observed_at,
            data={"macro_observation": data},
            metadata={
                **classification.metadata_fields(),
                "provenance": {
                    "observation_id": observation.canonical_id,
                    "source_id": observation.source_id,
                    "source_revision": observation.source_revision,
                    "source_schema_version": observation.schema_version,
                },
            },
        )
        return cls(payload=payload, observation_id=observation.canonical_id)


__all__ = ["ExternalMacroEvidenceProjection"]
