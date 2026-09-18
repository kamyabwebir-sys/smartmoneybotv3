from __future__ import annotations
from dataclasses import dataclass
from smart_money.application.token_candidate_safety_projection import TokenCandidateSafetyEvidenceProjection
from smart_money.application.token_safety_summary_input_binding import TokenSafetySummaryInputBinding
from smart_money.core.ids import deterministic_id

@dataclass(frozen=True, slots=True)
class TokenSafetySummaryReplayVerification:
    binding_id: str
    matches: bool
    verification_id: str
    schema_version: str = "token_safety_summary_replay_verification.v1"

    def __post_init__(self) -> None:
        expected = deterministic_id("token_safety_summary_replay_verification",
            {"binding_id": self.binding_id, "matches": self.matches, "schema_version": self.schema_version})
        if self.verification_id != expected:
            raise ValueError("verification_id mismatch")

def verify_token_safety_summary_replay(binding: TokenSafetySummaryInputBinding,
                                       projection: TokenCandidateSafetyEvidenceProjection) -> TokenSafetySummaryReplayVerification:
    rebuilt = TokenCandidateSafetyEvidenceProjection.from_binding(binding)
    matches = rebuilt.payload.get_canonical_id() == projection.payload.get_canonical_id()
    identity = {"binding_id": binding.binding_id, "matches": matches,
                "schema_version": "token_safety_summary_replay_verification.v1"}
    return TokenSafetySummaryReplayVerification(binding.binding_id, matches,
        deterministic_id("token_safety_summary_replay_verification", identity))

__all__ = ["TokenSafetySummaryReplayVerification", "verify_token_safety_summary_replay"]
