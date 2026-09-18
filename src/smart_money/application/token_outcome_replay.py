from __future__ import annotations
from dataclasses import dataclass
from smart_money.application.token_outcome_query import TokenOutcomeQueryResult
from smart_money.core.ids import deterministic_id

@dataclass(frozen=True, slots=True)
class TokenOutcomeReplayVerification:
    query_id: str
    replay_matches: bool
    verification_id: str
    schema_version: str = "token_outcome_replay_verification.v1"

    def __post_init__(self) -> None:
        expected = deterministic_id("token_outcome_replay_verification",
                                    {"query_id": self.query_id, "replay_matches": self.replay_matches,
                                     "schema_version": self.schema_version})
        if self.verification_id != expected:
            raise ValueError("verification_id mismatch")

def verify_token_outcome_replay(original: TokenOutcomeQueryResult,
                                replayed: TokenOutcomeQueryResult) -> TokenOutcomeReplayVerification:
    if not isinstance(original, TokenOutcomeQueryResult) or not isinstance(replayed, TokenOutcomeQueryResult):
        raise TypeError("results must be TokenOutcomeQueryResult")
    matches = original.query_id == replayed.query_id and original.rows == replayed.rows
    identity = {"query_id": original.query_id, "replay_matches": matches,
                "schema_version": "token_outcome_replay_verification.v1"}
    return TokenOutcomeReplayVerification(original.query_id, matches,
        deterministic_id("token_outcome_replay_verification", identity))

__all__ = ["TokenOutcomeReplayVerification", "verify_token_outcome_replay"]
