from __future__ import annotations
from dataclasses import dataclass
from smart_money.application.token_candidate_binding import TokenCandidateBinding
from smart_money.ingestion.contracts import EvidencePayload

@dataclass(frozen=True, slots=True)
class TokenCandidateLedgerProjection:
    payload: EvidencePayload
    candidate_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.payload, EvidencePayload):
            raise TypeError("payload must be EvidencePayload")
        if self.payload.evidence_type != "token_candidate":
            raise ValueError("unsupported evidence_type")
        if self.payload.data.get("candidate", {}).get("candidate_id") != self.candidate_id:
            raise ValueError("candidate_id mismatch")

    @classmethod
    def from_binding(cls, binding: TokenCandidateBinding) -> "TokenCandidateLedgerProjection":
        if not isinstance(binding, TokenCandidateBinding):
            raise TypeError("binding must be TokenCandidateBinding")
        payload = EvidencePayload(
            source_id="token-candidate",
            evidence_type="token_candidate",
            timestamp=0,
            data={"candidate": {
                "candidate_id": binding.candidate_id,
                "token_id": binding.token_id,
                "lifecycle_ids": list(binding.lifecycle_ids),
                "schema_version": binding.schema_version,
            }},
            metadata={"authority": "NONE", "classification": "EVIDENCE",
                      "verification_status": "UNKNOWN",
                      "provenance": {"candidate_id": binding.candidate_id}},
        )
        return cls(payload, binding.candidate_id)

__all__ = ["TokenCandidateLedgerProjection"]
