from __future__ import annotations
from dataclasses import dataclass
from smart_money.application.token_lifecycle import TokenLifecycle
from smart_money.application.token_outcome_query import TokenOutcomeQueryResult
from smart_money.core.ids import deterministic_id

@dataclass(frozen=True, slots=True)
class TokenCandidateBinding:
    token_id: str
    lifecycle_ids: tuple[str, ...]
    candidate_id: str
    schema_version: str = "token_candidate_binding.v1"

    def __post_init__(self) -> None:
        if not self.token_id.strip() or not self.lifecycle_ids:
            raise ValueError("token_id and lifecycle_ids are required")
        expected = deterministic_id("token_candidate_binding",
                                    {"lifecycle_ids": self.lifecycle_ids, "schema_version": self.schema_version,
                                     "token_id": self.token_id.strip()})
        if self.candidate_id != expected:
            raise ValueError("candidate_id mismatch")

def bind_token_candidate(token_id: str, lifecycles: tuple[TokenLifecycle, ...],
                         outcome: TokenOutcomeQueryResult | None = None) -> TokenCandidateBinding:
    if not isinstance(token_id, str) or not token_id.strip():
        raise ValueError("token_id must be non-empty")
    if not isinstance(lifecycles, tuple) or not lifecycles or not all(isinstance(x, TokenLifecycle) for x in lifecycles):
        raise TypeError("lifecycles must be non-empty tuple")
    if any(x.token_id.strip() != token_id.strip() for x in lifecycles):
        raise ValueError("token_id mismatch")
    ids = tuple(x.lifecycle_id for x in lifecycles)
    identity = {"lifecycle_ids": ids, "schema_version": "token_candidate_binding.v1", "token_id": token_id.strip()}
    return TokenCandidateBinding(token_id, ids, deterministic_id("token_candidate_binding", identity))

__all__ = ["TokenCandidateBinding", "bind_token_candidate"]
