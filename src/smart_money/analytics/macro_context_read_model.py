from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from smart_money.analytics.macro_context_binding import (
    AnalyticsSubjectKind,
    MacroContextBinding,
)
from smart_money.analytics.macro_context_projection import MacroContextStatus
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class MacroContextReadModel:
    """Canonical read projection for Token/Wallet dashboards and reports."""

    subject_kind: AnalyticsSubjectKind
    subject_id: str
    binding_id: str
    context_id: str
    metric: str
    context_status: MacroContextStatus
    observation_count: int
    conflicted_count: int
    unknown_count: int
    latest_observed_at: int | None
    latest_value: Decimal | None
    latest_unit: str | None
    latest_source_id: str | None
    latest_source_revision: str | None
    explanation_code: str
    schema_version: str = "macro_context_read_model.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.subject_kind, AnalyticsSubjectKind):
            raise TypeError("subject_kind must be an AnalyticsSubjectKind")
        for field_name in (
            "subject_id",
            "binding_id",
            "context_id",
            "metric",
            "explanation_code",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if not isinstance(self.context_status, MacroContextStatus):
            raise TypeError("context_status must be a MacroContextStatus")
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
        if self.latest_observed_at is not None and (
            isinstance(self.latest_observed_at, bool)
            or not isinstance(self.latest_observed_at, int)
            or self.latest_observed_at < 0
        ):
            raise ValueError("latest_observed_at must be a non-negative integer")
        if self.latest_value is not None and (
            not isinstance(self.latest_value, Decimal)
            or not self.latest_value.is_finite()
        ):
            raise TypeError("latest_value must be a finite Decimal")
        for field_name in (
            "latest_unit",
            "latest_source_id",
            "latest_source_revision",
        ):
            value = getattr(self, field_name)
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                raise ValueError(f"{field_name} must be non-empty when present")
        if self.observation_count == 0 and self.latest_observed_at is not None:
            raise ValueError("missing context cannot have latest observation data")
        if self.observation_count > 0 and self.latest_observed_at is None:
            raise ValueError("non-empty context requires latest observation data")
        if self.schema_version != "macro_context_read_model.v1":
            raise ValueError("unsupported macro context read model schema_version")

    @classmethod
    def from_binding(cls, binding: MacroContextBinding) -> MacroContextReadModel:
        if not isinstance(binding, MacroContextBinding):
            raise TypeError("binding must be a MacroContextBinding")
        context = binding.context
        latest = context.latest_observation
        if context.status is MacroContextStatus.MISSING:
            explanation_code = "MACRO_CONTEXT_MISSING"
        elif context.status is MacroContextStatus.CONFLICTED:
            explanation_code = "MACRO_CONTEXT_CONFLICTED"
        else:
            explanation_code = "MACRO_CONTEXT_AVAILABLE"
        return cls(
            subject_kind=binding.subject_kind,
            subject_id=binding.subject_id,
            binding_id=binding.canonical_id,
            context_id=context.canonical_id,
            metric=context.metric,
            context_status=context.status,
            observation_count=context.observation_count,
            conflicted_count=context.conflicted_count,
            unknown_count=context.unknown_count,
            latest_observed_at=None if latest is None else latest.observed_at,
            latest_value=None if latest is None else latest.value,
            latest_unit=None if latest is None else latest.unit,
            latest_source_id=None if latest is None else latest.source_id,
            latest_source_revision=(
                None if latest is None else latest.source_revision
            ),
            explanation_code=explanation_code,
        )

    @property
    def missing(self) -> bool:
        return self.context_status is MacroContextStatus.MISSING

    @property
    def conflicted(self) -> bool:
        return self.context_status is MacroContextStatus.CONFLICTED

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "binding_id": self.binding_id,
            "conflicted_count": self.conflicted_count,
            "context_id": self.context_id,
            "context_status": self.context_status,
            "explanation_code": self.explanation_code,
            "latest_observed_at": self.latest_observed_at,
            "latest_source_id": self.latest_source_id,
            "latest_source_revision": self.latest_source_revision,
            "latest_unit": self.latest_unit,
            "latest_value": self.latest_value,
            "metric": self.metric,
            "observation_count": self.observation_count,
            "schema_version": self.schema_version,
            "subject_id": self.subject_id,
            "subject_kind": self.subject_kind,
            "unknown_count": self.unknown_count,
        }

    @property
    def canonical_id(self) -> str:
        return deterministic_id("macro_context_read_model", self.canonical_dict())


__all__ = ["MacroContextReadModel"]
