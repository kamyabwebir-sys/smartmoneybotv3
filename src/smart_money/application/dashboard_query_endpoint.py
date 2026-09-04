from __future__ import annotations

from dataclasses import dataclass

from smart_money.application.dashboard_macro_read_index import (
    DashboardMacroReadIndex,
)
from smart_money.application.dashboard_query_audit_receipt import (
    DashboardQueryAuditReceipt,
)
from smart_money.application.dashboard_query_error import DashboardQueryError
from smart_money.application.dashboard_query_result import (
    DashboardQueryResult,
)
from smart_money.application.dashboard_subject_detail_query import (
    DashboardSubjectDetailQuery,
)


@dataclass(frozen=True, slots=True)
class DashboardQueryEndpoint:
    """Application adapter exposing canonical dashboard query results."""

    index: DashboardMacroReadIndex
    schema_version: str = "dashboard_query_endpoint.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.index, DashboardMacroReadIndex):
            raise TypeError("index must be a DashboardMacroReadIndex")
        if self.schema_version != "dashboard_query_endpoint.v1":
            raise ValueError("unsupported dashboard query endpoint schema_version")

    def execute(
        self,
        query: DashboardSubjectDetailQuery,
    ) -> DashboardQueryResult:
        if not isinstance(query, DashboardSubjectDetailQuery):
            raise TypeError("query must be a DashboardSubjectDetailQuery")
        return self.index.result_for_query(query)

    def execute_safe(
        self,
        query: DashboardSubjectDetailQuery,
    ) -> DashboardQueryResult | DashboardQueryError:
        try:
            return self.execute(query)
        except (KeyError, TypeError, ValueError) as exception:
            safe_query = query if isinstance(query, DashboardSubjectDetailQuery) else None
            return DashboardQueryError.from_exception(exception, safe_query)

    def execute_with_receipt(
        self,
        query: DashboardSubjectDetailQuery,
    ) -> tuple[
        DashboardQueryResult | DashboardQueryError,
        DashboardQueryAuditReceipt,
    ]:
        outcome = self.execute_safe(query)
        return outcome, DashboardQueryAuditReceipt.from_outcome(outcome)


__all__ = ["DashboardQueryEndpoint"]
