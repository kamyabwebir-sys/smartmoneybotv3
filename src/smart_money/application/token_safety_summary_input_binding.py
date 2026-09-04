from __future__ import annotations
from dataclasses import dataclass
from smart_money.application.token_candidate_binding import TokenCandidateBinding
from smart_money.application.token_safety_evidence_summary import TokenSafetyEvidenceSummary
from smart_money.core.ids import deterministic_id

@dataclass(frozen=True, slots=True)
class TokenSafetySummaryInputBinding:
    candidate_id: str
    summary_id: str
    binding_id: str
    schema_version: str = "token_safety_summary_input_binding.v1"

    def __post_init__(self) -> None:
        if not self.candidate_id.strip() or not self.summary_id.strip():
            raise ValueError("candidate_id and summary_id are required")
        if self.binding_id != deterministic_id("token_safety_summary_input_binding",
            {"candidate_id": self.candidate_id.strip(), "schema_version": self.schema_version, "summary_id": self.summary_id.strip()}):
            raise ValueError("binding_id mismatch")

def bind_token_safety_summary_input(candidate: TokenCandidateBinding,
                                    summary: TokenSafetyEvidenceSummary) -> TokenSafetySummaryInputBinding:
    if not isinstance(candidate, TokenCandidateBinding) or not isinstance(summary, TokenSafetyEvidenceSummary):
        raise TypeError("candidate and summary types are invalid")
    identity = {"candidate_id": candidate.candidate_id, "schema_version": "token_safety_summary_input_binding.v1", "summary_id": summary.summary_id}
    return TokenSafetySummaryInputBinding(candidate.candidate_id, summary.summary_id,
        deterministic_id("token_safety_summary_input_binding", identity))

__all__ = ["TokenSafetySummaryInputBinding", "bind_token_safety_summary_input"]
