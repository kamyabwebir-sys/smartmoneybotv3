from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.dashboard_subject_detail_query import (
    DashboardSubjectDetailQuery,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class DashboardQueryError:
    """Canonical fail-closed error envelope for dashboard queries."""

    error_code: str
    message: str
    query_id: str | None = None
    schema_version: str = "dashboard_query_error.v1"

    def __post_init__(self) -> None:
        for field_name in ("error_code", "message"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if self.query_id is not None and (
            not isinstance(self.query_id, str) or not self.query_id.strip()
        ):
            raise ValueError("query_id must be a non-empty string or None")
        if self.schema_version != "dashboard_query_error.v1":
            raise ValueError("unsupported dashboard query error schema_version")

    @classmethod
    def from_exception(
        cls,
        exception: Exception,
        query: DashboardSubjectDetailQuery | None = None,
    ) -> DashboardQueryError:
        if isinstance(exception, KeyError):
            code = "SUBJECT_NOT_FOUND"
        elif isinstance(exception, TypeError):
            code = "INVALID_QUERY"
        elif isinstance(exception, ValueError):
            code = "QUERY_CONFLICT"
        else:
            code = "QUERY_FAILURE"
        return cls(
            error_code=code,
            message=str(exception).strip() or exception.__class__.__name__,
            query_id=None if query is None else query.query_id,
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "query_id": self.query_id,
            "schema_version": self.schema_version,
        }

    @property
    def error_id(self) -> str:
        return deterministic_id(
            "dashboard_query_error",
            self.canonical_dict(),
        )


__all__ = ["DashboardQueryError"]
