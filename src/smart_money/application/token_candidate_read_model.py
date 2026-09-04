from __future__ import annotations
from dataclasses import dataclass
from smart_money.application.token_candidate_binding import TokenCandidateBinding

@dataclass(frozen=True, slots=True)
class TokenCandidateReadModel:
    rows: tuple[TokenCandidateBinding, ...]
    schema_version: str = "token_candidate_read_model.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple) or not all(isinstance(row, TokenCandidateBinding) for row in self.rows):
            raise TypeError("rows must be tuple of TokenCandidateBinding")

def build_token_candidate_read_model(rows: tuple[TokenCandidateBinding, ...]) -> TokenCandidateReadModel:
    return TokenCandidateReadModel(rows)

__all__ = ["TokenCandidateReadModel", "build_token_candidate_read_model"]
