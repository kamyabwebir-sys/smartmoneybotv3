from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from smart_money.domain.macro_context import MacroEvidenceObservation


@runtime_checkable
class MacroEvidenceProvider(Protocol):
    """Application port for replayable, external macro observations."""

    def observations(
        self,
        *,
        metric: str,
        start_at: int,
        end_at: int,
    ) -> Iterable[MacroEvidenceObservation]:
        """Return deterministic observations for one bounded time window."""
        ...


__all__ = ["MacroEvidenceProvider"]
