from __future__ import annotations
from dataclasses import dataclass
from smart_money.application.token_lifecycle_outcome_window import TokenLifecycleOutcomeWindow

@dataclass(frozen=True, slots=True)
class TokenOutcomeWindowReadModel:
    rows: tuple[TokenLifecycleOutcomeWindow, ...]
    schema_version: str = "token_outcome_window_read_model.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple) or not all(isinstance(row, TokenLifecycleOutcomeWindow) for row in self.rows):
            raise TypeError("rows must be tuple of TokenLifecycleOutcomeWindow")

def build_token_outcome_window_read_model(
    rows: tuple[TokenLifecycleOutcomeWindow, ...],
) -> TokenOutcomeWindowReadModel:
    return TokenOutcomeWindowReadModel(rows)

__all__ = ["TokenOutcomeWindowReadModel", "build_token_outcome_window_read_model"]
