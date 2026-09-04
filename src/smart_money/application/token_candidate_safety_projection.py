from __future__ import annotations
from dataclasses import dataclass
from smart_money.application.token_safety_summary_input_binding import TokenSafetySummaryInputBinding
from smart_money.ingestion.contracts import EvidencePayload

@dataclass(frozen=True, slots=True)
class TokenCandidateSafetyEvidenceProjection:
    payload: EvidencePayload
    binding_id: str

    @classmethod
    def from_binding(cls, binding: TokenSafetySummaryInputBinding) -> "TokenCandidateSafetyEvidenceProjection":
        if not isinstance(binding, TokenSafetySummaryInputBinding):
            raise TypeError("binding must be TokenSafetySummaryInputBinding")
        payload = EvidencePayload(
            source_id="token-safety-summary",
            evidence_type="token_candidate_safety_summary",
            data={"binding": {"candidate_id": binding.candidate_id, "summary_id": binding.summary_id, "binding_id": binding.binding_id}},
            metadata={"authority": "NONE", "classification": "EVIDENCE", "verification_status": "UNKNOWN",
                      "provenance": {"binding_id": binding.binding_id}},
        )
        return cls(payload, binding.binding_id)

__all__ = ["TokenCandidateSafetyEvidenceProjection"]
