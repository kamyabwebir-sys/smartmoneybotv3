from __future__ import annotations
from dataclasses import dataclass
from smart_money.application.token_candidate_binding import TokenCandidateBinding
from smart_money.application.token_candidate_ledger_projection import TokenCandidateLedgerProjection
from smart_money.core.ids import deterministic_id

@dataclass(frozen=True, slots=True)
class TokenCandidateReplayVerification:
    candidate_id: str
    replay_matches: bool
    verification_id: str
    schema_version: str = "token_candidate_replay_verification.v1"

    def __post_init__(self) -> None:
        expected = deterministic_id("token_candidate_replay_verification",
            {"candidate_id": self.candidate_id, "replay_matches": self.replay_matches,
             "schema_version": self.schema_version})
        if self.verification_id != expected:
            raise ValueError("verification_id mismatch")

def verify_token_candidate_replay(binding: TokenCandidateBinding,
                                  projection: TokenCandidateLedgerProjection) -> TokenCandidateReplayVerification:
    rebuilt = TokenCandidateLedgerProjection.from_binding(binding)
    matches = rebuilt.payload.get_canonical_id() == projection.payload.get_canonical_id()
    identity = {"candidate_id": projection.candidate_id, "replay_matches": matches,
                "schema_version": "token_candidate_replay_verification.v1"}
    return TokenCandidateReplayVerification(projection.candidate_id, matches,
        deterministic_id("token_candidate_replay_verification", identity))

__all__ = ["TokenCandidateReplayVerification", "verify_token_candidate_replay"]
