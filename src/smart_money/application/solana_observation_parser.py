from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar

from smart_money.core.serialization import canonicalize
from smart_money.domain.solana_observation import SolanaChainObservation
from smart_money.domain.truth import TruthClassification
from smart_money.ingestion.contracts import EvidencePayload

_CLASSIFICATION = TruthClassification.canonical_observation()


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    return value


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return value


@dataclass(frozen=True, slots=True)
class SolanaObservationParser:
    """Typed parser/projector for canonical Solana chain observations."""

    EVIDENCE_TYPE: ClassVar[str] = "solana_chain_observation"
    payload: EvidencePayload
    observation_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.payload, EvidencePayload):
            raise TypeError("payload must be an EvidencePayload")
        if self.payload.evidence_type != self.EVIDENCE_TYPE:
            raise ValueError("unsupported Solana observation evidence_type")
        data = _mapping(
            self.payload.data.get("solana_observation"),
            "solana_observation",
        )
        provenance = _mapping(self.payload.metadata.get("provenance"), "provenance")
        if set(self.payload.data) != {"solana_observation"}:
            raise ValueError("Solana observation data keys do not match")
        if set(self.payload.metadata) != {
            "authority",
            "classification",
            "provenance",
            "verification_status",
        }:
            raise ValueError("Solana observation metadata keys do not match")
        if canonicalize(_CLASSIFICATION.metadata_fields()) != canonicalize(
            {
                "authority": self.payload.metadata["authority"],
                "classification": self.payload.metadata["classification"],
                "verification_status": self.payload.metadata["verification_status"],
            }
        ):
            raise ValueError("Solana observation classification mismatch")
        if data.get("observation_id") != self.observation_id:
            raise ValueError("Solana observation identity mismatch")
        expected_provenance = {
            "observation_id": self.observation_id,
            "source_id": self.payload.source_id,
            "source_schema_version": SolanaChainObservation.__dataclass_fields__[
                "schema_version"
            ].default,
        }
        if canonicalize(provenance) != canonicalize(expected_provenance):
            raise ValueError("Solana observation provenance mismatch")

    @classmethod
    def from_observation(
        cls,
        observation: SolanaChainObservation,
    ) -> SolanaObservationParser:
        if not isinstance(observation, SolanaChainObservation):
            raise TypeError("observation must be a SolanaChainObservation")
        payload = EvidencePayload(
            source_id="solana",
            evidence_type=cls.EVIDENCE_TYPE,
            timestamp=observation.observed_at,
            data={
                "solana_observation": {
                    **observation.canonical_dict(),
                    "observation_id": observation.observation_id,
                }
            },
            metadata={
                **_CLASSIFICATION.metadata_fields(),
                "provenance": {
                    "observation_id": observation.observation_id,
                    "source_id": "solana",
                    "source_schema_version": observation.schema_version,
                },
            },
        )
        return cls(payload=payload, observation_id=observation.observation_id)

    @classmethod
    def from_payload(cls, payload: EvidencePayload) -> SolanaObservationParser:
        if not isinstance(payload, EvidencePayload):
            raise TypeError("payload must be an EvidencePayload")
        data = _mapping(payload.data.get("solana_observation"), "solana_observation")
        return cls(
            payload=payload,
            observation_id=_text(data.get("observation_id"), "observation_id"),
        )

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> SolanaObservationParser:
        if not isinstance(raw, Mapping):
            raise TypeError("raw observation must be a mapping")
        allowed = {
            "slot",
            "observed_at",
            "transaction_signature",
            "program_id",
            "subject",
            "facts",
            "commitment",
        }
        if set(raw) != allowed:
            raise ValueError("raw Solana observation keys do not match schema")
        observation = SolanaChainObservation(
            slot=_integer(raw["slot"], "slot"),
            observed_at=_integer(raw["observed_at"], "observed_at"),
            transaction_signature=_text(
                raw["transaction_signature"], "transaction_signature"
            ),
            program_id=_text(raw["program_id"], "program_id"),
            subject=_text(raw["subject"], "subject"),
            facts=_mapping(raw["facts"], "facts"),
            commitment=_text(raw["commitment"], "commitment"),
        )
        return cls.from_observation(observation)


__all__ = ["SolanaObservationParser"]
