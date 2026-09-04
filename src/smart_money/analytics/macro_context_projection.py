from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from smart_money.core.ids import deterministic_id
from smart_money.domain.macro_context import (
    MacroEvidenceObservation,
)


@runtime_checkable
class MacroEvidenceWindowLike(Protocol):
    metric: str
    start_at: int
    end_at: int
    observations: tuple[MacroEvidenceObservation, ...]
    conflicted_count: int
    unknown_count: int


class MacroContextStatus(str, Enum):
    MISSING = "MISSING"
    CONFIRMED = "CONFIRMED"
    PROVISIONAL = "PROVISIONAL"
    CONFLICTED = "CONFLICTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class MacroAnalyticsContext:
    """Read-only macro context for Analytics; it never makes a decision."""

    metric: str
    start_at: int
    end_at: int
    latest_observation: MacroEvidenceObservation | None
    status: MacroContextStatus
    observation_count: int
    conflicted_count: int
    unknown_count: int
    schema_version: str = "macro_analytics_context.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.metric, str) or not self.metric.strip():
            raise ValueError("metric must be a non-empty string")
        if isinstance(self.start_at, bool) or not isinstance(self.start_at, int):
            raise TypeError("start_at must be an integer")
        if isinstance(self.end_at, bool) or not isinstance(self.end_at, int):
            raise TypeError("end_at must be an integer")
        if self.start_at > self.end_at:
            raise ValueError("start_at must not exceed end_at")
        if self.latest_observation is not None and not isinstance(
            self.latest_observation,
            MacroEvidenceObservation,
        ):
            raise TypeError("latest_observation must be a MacroEvidenceObservation")
        if not isinstance(self.status, MacroContextStatus):
            raise TypeError("status must be a MacroContextStatus")
        for field_name in (
            "observation_count",
            "conflicted_count",
            "unknown_count",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field_name} must be an integer")
            if value < 0:
                raise ValueError(f"{field_name} must be non-negative")
        if self.observation_count == 0 and self.latest_observation is not None:
            raise ValueError("empty context cannot have a latest observation")
        if self.observation_count > 0 and self.latest_observation is None:
            raise ValueError("non-empty context requires a latest observation")
        if self.schema_version != "macro_analytics_context.v1":
            raise ValueError("unsupported macro analytics context schema_version")

    @classmethod
    def from_window(
        cls,
        window: MacroEvidenceWindowLike,
    ) -> MacroAnalyticsContext:
        if not isinstance(window, MacroEvidenceWindowLike):
            raise TypeError("window must satisfy the macro evidence window contract")
        latest = window.observations[-1] if window.observations else None
        if not window.observations:
            status = MacroContextStatus.MISSING
        elif window.conflicted_count > 0:
            status = MacroContextStatus.CONFLICTED
        else:
            status = MacroContextStatus(latest.status.value)
        return cls(
            metric=window.metric,
            start_at=window.start_at,
            end_at=window.end_at,
            latest_observation=latest,
            status=status,
            observation_count=window.matched_count,
            conflicted_count=window.conflicted_count,
            unknown_count=window.unknown_count,
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "conflicted_count": self.conflicted_count,
            "end_at": self.end_at,
            "latest_observation": (
                None
                if self.latest_observation is None
                else self.latest_observation.canonical_dict()
            ),
            "metric": self.metric,
            "observation_count": self.observation_count,
            "schema_version": self.schema_version,
            "start_at": self.start_at,
            "status": self.status,
            "unknown_count": self.unknown_count,
        }

    @property
    def canonical_id(self) -> str:
        return deterministic_id("macro_analytics_context", self.canonical_dict())


__all__ = ["MacroAnalyticsContext", "MacroContextStatus"]
