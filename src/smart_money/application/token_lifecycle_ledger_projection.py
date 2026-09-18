from __future__ import annotations

from dataclasses import dataclass

from smart_money.application.token_lifecycle_observation_binding import TokenLifecycleObservationBinding
from smart_money.ingestion.contracts import EvidencePayload


@dataclass(frozen=True, slots=True)
class TokenLifecycleLedgerProjection:
    payload: EvidencePayload
    lifecycle_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.payload, EvidencePayload):
            raise TypeError("payload must be EvidencePayload")
        if self.payload.evidence_type != "token_lifecycle":
            raise ValueError("unsupported evidence_type")
        if self.payload.data.get("lifecycle", {}).get("lifecycle_id") != self.lifecycle_id:
            raise ValueError("lifecycle_id mismatch")

    @classmethod
    def from_binding(cls, binding: TokenLifecycleObservationBinding) -> "TokenLifecycleLedgerProjection":
        if not isinstance(binding, TokenLifecycleObservationBinding):
            raise TypeError("binding must be TokenLifecycleObservationBinding")
        lifecycle = binding.lifecycle
        payload = EvidencePayload(
            source_id="token-lifecycle",
            evidence_type="token_lifecycle",
            timestamp=lifecycle.observed_slot,
            data={"lifecycle": lifecycle.canonical_dict()},
            metadata={
                "authority": "NONE",
                "classification": "EVIDENCE",
                "verification_status": "UNKNOWN",
                "provenance": {
                    "lifecycle_id": lifecycle.lifecycle_id,
                    "observation_ids": ",".join(binding.observation_ids),
                },
            },
        )
        return cls(payload, lifecycle.lifecycle_id)


__all__ = ["TokenLifecycleLedgerProjection"]
