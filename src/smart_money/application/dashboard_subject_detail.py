from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.dashboard_macro_read_endpoint import (
    DashboardMacroReadResponse,
)
from smart_money.core.ids import deterministic_id


def _line_value(markdown: str, prefix: str) -> str:
    for line in markdown.splitlines():
        if line.startswith(prefix):
            value = line[len(prefix) :].strip()
            if value.startswith("`") and value.endswith("`"):
                value = value[1:-1]
            if value:
                return value
    raise ValueError(f"dashboard report is missing {prefix!r}")


def _observation_values(markdown: str) -> dict[str, str]:
    lines = markdown.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != "| شاخص | وضعیت | زمان مشاهده | مقدار | واحد |":
            continue
        for row in lines[index + 2 :]:
            if not row.startswith("|") or row == "":
                continue
            parts = [part.strip() for part in row.strip("|").split("|")]
            if len(parts) == 5:
                return dict(
                    zip(
                        ("شاخص", "وضعیت", "زمان مشاهده", "مقدار", "واحد"),
                        parts,
                        strict=True,
                    )
                )
    raise ValueError("dashboard report is missing observation table")


def _table_value(values: dict[str, str], label: str) -> str:
    value = values.get(label, "")
    if value:
        return value
    raise ValueError(f"dashboard report is missing table value {label!r}")


def _summary_value(markdown: str, label: str) -> str:
    for line in markdown.splitlines():
        if line.startswith(f"| {label} |"):
            parts = [part.strip() for part in line.strip("|").split("|")]
            if len(parts) == 2 and parts[1]:
                return parts[1].strip("`")
    raise ValueError(f"dashboard report is missing summary value {label!r}")


@dataclass(frozen=True, slots=True)
class DashboardSubjectDetail:
    """Canonical, read-only detail projection for one dashboard subject."""

    response: DashboardMacroReadResponse
    subject_kind: str
    context_status: str
    metric: str
    latest_observed_at: str
    latest_value: str
    latest_unit: str
    observation_count: int
    conflicted_count: int
    unknown_count: int
    schema_version: str = "dashboard_subject_detail.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.response, DashboardMacroReadResponse):
            raise TypeError("response must be a DashboardMacroReadResponse")
        for field_name in (
            "subject_kind",
            "context_status",
            "metric",
            "latest_observed_at",
            "latest_value",
            "latest_unit",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        for field_name in (
            "observation_count",
            "conflicted_count",
            "unknown_count",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")
        if self.schema_version != "dashboard_subject_detail.v1":
            raise ValueError("unsupported dashboard subject detail schema_version")

    @classmethod
    def from_response(
        cls,
        response: DashboardMacroReadResponse,
    ) -> DashboardSubjectDetail:
        if not isinstance(response, DashboardMacroReadResponse):
            raise TypeError("response must be a DashboardMacroReadResponse")
        markdown = response.markdown
        observation_values = _observation_values(markdown)
        return cls(
            response=response,
            subject_kind=response.subject_kind,
            context_status=_table_value(observation_values, "وضعیت"),
            metric=_table_value(observation_values, "شاخص"),
            latest_observed_at=_table_value(observation_values, "زمان مشاهده"),
            latest_value=_table_value(observation_values, "مقدار"),
            latest_unit=_table_value(observation_values, "واحد"),
            observation_count=int(
                _summary_value(markdown, "تعداد مشاهده‌ها")
            ),
            conflicted_count=int(
                _summary_value(markdown, "تعداد موارد متناقض")
            ),
            unknown_count=int(_summary_value(markdown, "تعداد موارد نامشخص")),
        )

    @property
    def subject_id(self) -> str:
        return self.response.subject_id

    @property
    def detail_id(self) -> str:
        return deterministic_id(
            "dashboard_subject_detail",
            self.canonical_dict(),
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "conflicted_count": self.conflicted_count,
            "context_status": self.context_status,
            "latest_observed_at": self.latest_observed_at,
            "latest_unit": self.latest_unit,
            "latest_value": self.latest_value,
            "metric": self.metric,
            "observation_count": self.observation_count,
            "response_id": self.response.response_id,
            "schema_version": self.schema_version,
            "subject_id": self.subject_id,
            "subject_kind": self.subject_kind,
            "unknown_count": self.unknown_count,
        }


__all__ = ["DashboardSubjectDetail"]
