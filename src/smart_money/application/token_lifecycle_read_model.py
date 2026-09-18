from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from smart_money.application.token_lifecycle import TokenLifecycle


@dataclass(frozen=True, slots=True)
class TokenLifecycleReadRow:
    lifecycle: TokenLifecycle

    def canonical_dict(self) -> dict[str, Any]:
        return self.lifecycle.canonical_dict()


@dataclass(frozen=True, slots=True)
class TokenLifecycleReadModel:
    rows: tuple[TokenLifecycleReadRow, ...]
    schema_version: str = "token_lifecycle_read_model.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple) or not all(isinstance(row, TokenLifecycleReadRow) for row in self.rows):
            raise TypeError("rows must be tuple of TokenLifecycleReadRow")


def build_token_lifecycle_read_model(lifecycles: tuple[TokenLifecycle, ...]) -> TokenLifecycleReadModel:
    if not isinstance(lifecycles, tuple) or not all(isinstance(item, TokenLifecycle) for item in lifecycles):
        raise TypeError("lifecycles must be tuple of TokenLifecycle")
    return TokenLifecycleReadModel(tuple(TokenLifecycleReadRow(item) for item in lifecycles))


__all__ = ["TokenLifecycleReadModel", "TokenLifecycleReadRow", "build_token_lifecycle_read_model"]
