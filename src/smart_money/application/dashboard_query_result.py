from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from smart_money.application.dashboard_macro_read_index import (
    DashboardMacroReadPage,
)
from smart_money.application.dashboard_subject_detail_query import (
    DashboardSubjectDetailQuery,
)
from smart_money.core.ids import deterministic_id


class DashboardQueryResultStatus(str, Enum):
    SUCCESS = "SUCCESS"
    EMPTY = "EMPTY"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True, slots=True)
class DashboardQueryResult:
    """Canonical result envelope for dashboard detail queries."""

    query: DashboardSubjectDetailQuery
    page: DashboardMacroReadPage
    status: DashboardQueryResultStatus
    error_code: str | None = None
    schema_version: str = "dashboard_query_result.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.query, DashboardSubjectDetailQuery):
            raise TypeError("query must be a DashboardSubjectDetailQuery")
        if not isinstance(self.page, DashboardMacroReadPage):
            raise TypeError("page must be a DashboardMacroReadPage")
        if not isinstance(self.status, DashboardQueryResultStatus):
            raise TypeError("status must be a DashboardQueryResultStatus")
        if self.page.query != self.query.query:
            raise ValueError("page query does not match query contract")
        if self.page.offset != self.query.offset:
            raise ValueError("page offset does not match query contract")
        if self.page.limit != self.query.limit:
            raise ValueError("page limit does not match query contract")
        if self.error_code is not None and (
            not isinstance(self.error_code, str) or not self.error_code.strip()
        ):
            raise ValueError("error_code must be a non-empty string or None")
        expected_status = (
            DashboardQueryResultStatus.EMPTY
            if self.page.total_count == 0
            else DashboardQueryResultStatus.SUCCESS
        )
        if self.status is not DashboardQueryResultStatus.CONFLICT:
            if self.status is not expected_status:
                raise ValueError("status does not match page contents")
            if self.error_code is not None:
                raise ValueError("success or empty result cannot have error_code")
        elif self.error_code is None:
            raise ValueError("conflict result requires error_code")
        if self.schema_version != "dashboard_query_result.v1":
            raise ValueError("unsupported dashboard query result schema_version")

    @classmethod
    def from_page(
        cls,
        query: DashboardSubjectDetailQuery,
        page: DashboardMacroReadPage,
    ) -> DashboardQueryResult:
        status = (
            DashboardQueryResultStatus.EMPTY
            if page.total_count == 0
            else DashboardQueryResultStatus.SUCCESS
        )
        return cls(query=query, page=page, status=status)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "page": self.page.canonical_dict(),
            "query": self.query.canonical_dict(),
            "schema_version": self.schema_version,
            "status": self.status.value,
        }

    @property
    def result_id(self) -> str:
        return deterministic_id(
            "dashboard_query_result",
            self.canonical_dict(),
        )


__all__ = ["DashboardQueryResult", "DashboardQueryResultStatus"]
