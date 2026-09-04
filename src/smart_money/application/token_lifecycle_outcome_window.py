from __future__ import annotations
from dataclasses import dataclass
from smart_money.application.token_lifecycle import TokenLifecycle, TokenLifecycleState, advance_token_lifecycle

@dataclass(frozen=True, slots=True)
class TokenLifecycleOutcomeWindow:
    lifecycle: TokenLifecycle
    close_slot: int
    schema_version: str = "token_lifecycle_outcome_window.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.lifecycle, TokenLifecycle):
            raise TypeError("lifecycle must be TokenLifecycle")
        if isinstance(self.close_slot, bool) or not isinstance(self.close_slot, int) or self.close_slot < self.lifecycle.observed_slot:
            raise ValueError("close_slot must not precede lifecycle slot")

def bind_outcome_window(lifecycle: TokenLifecycle, *, close_slot: int, evidence_ids: tuple[str, ...]) -> TokenLifecycleOutcomeWindow:
    updated = advance_token_lifecycle(lifecycle, state=TokenLifecycleState.OUTCOME_WINDOW_CLOSED,
                                       observed_slot=close_slot, evidence_ids=evidence_ids)
    return TokenLifecycleOutcomeWindow(updated, close_slot)

__all__ = ["TokenLifecycleOutcomeWindow", "bind_outcome_window"]
