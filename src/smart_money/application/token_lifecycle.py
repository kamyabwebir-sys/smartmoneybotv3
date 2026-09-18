from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from smart_money.core.ids import deterministic_id


class TokenLifecycleState(str, Enum):
    CREATED = "CREATED"
    METADATA_OBSERVED = "METADATA_OBSERVED"
    FIRST_LIQUIDITY = "FIRST_LIQUIDITY"
    FIRST_MEANINGFUL_SWAP = "FIRST_MEANINGFUL_SWAP"
    HOLDER_SHIFT = "HOLDER_SHIFT"
    AUTHORITY_CHANGE = "AUTHORITY_CHANGE"
    OUTCOME_WINDOW_CLOSED = "OUTCOME_WINDOW_CLOSED"


_ORDER = {state: index for index, state in enumerate(TokenLifecycleState)}


@dataclass(frozen=True, slots=True)
class TokenLifecycle:
    token_id: str
    state: TokenLifecycleState
    observed_slot: int
    evidence_ids: tuple[str, ...]
    lifecycle_id: str
    schema_version: str = "token_lifecycle.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.token_id, str) or not self.token_id.strip():
            raise ValueError("token_id must be non-empty")
        if not isinstance(self.state, TokenLifecycleState):
            raise TypeError("state must be TokenLifecycleState")
        if isinstance(self.observed_slot, bool) or not isinstance(self.observed_slot, int) or self.observed_slot < 0:
            raise ValueError("observed_slot must be non-negative")
        if not isinstance(self.evidence_ids, tuple) or not self.evidence_ids or any(
            not isinstance(item, str) or not item.strip() for item in self.evidence_ids
        ) or len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("evidence_ids must be unique non-empty tuple")
        if self.schema_version != "token_lifecycle.v1":
            raise ValueError("unsupported schema_version")
        if self.lifecycle_id != deterministic_id("token_lifecycle", self._identity()):
            raise ValueError("lifecycle_id does not match lifecycle")

    def _identity(self) -> dict[str, Any]:
        return {
            "evidence_ids": self.evidence_ids,
            "observed_slot": self.observed_slot,
            "schema_version": self.schema_version,
            "state": self.state.value,
            "token_id": self.token_id.strip(),
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {**self._identity(), "lifecycle_id": self.lifecycle_id}


def build_token_lifecycle(
    token_id: str,
    state: TokenLifecycleState,
    observed_slot: int,
    evidence_ids: tuple[str, ...],
) -> TokenLifecycle:
    identity = {
        "evidence_ids": evidence_ids,
        "observed_slot": observed_slot,
        "schema_version": "token_lifecycle.v1",
        "state": state.value,
        "token_id": token_id.strip(),
    }
    return TokenLifecycle(token_id, state, observed_slot, evidence_ids,
                          deterministic_id("token_lifecycle", identity))


def advance_token_lifecycle(current: TokenLifecycle, *, state: TokenLifecycleState,
                            observed_slot: int, evidence_ids: tuple[str, ...]) -> TokenLifecycle:
    if not isinstance(current, TokenLifecycle):
        raise TypeError("current must be TokenLifecycle")
    if _ORDER[state] < _ORDER[current.state] or observed_slot < current.observed_slot:
        raise ValueError("lifecycle cannot regress")
    return build_token_lifecycle(current.token_id, state, observed_slot, evidence_ids)


__all__ = ["TokenLifecycle", "TokenLifecycleState", "advance_token_lifecycle", "build_token_lifecycle"]
