from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from smart_money.application.dashboard_macro_read_endpoint import (
    DashboardMacroReadResponse,
)
from smart_money.application.dashboard_subject_detail import (
    DashboardSubjectDetail,
)
from smart_money.application.dashboard_subject_detail_query import (
    DashboardSubjectDetailQuery,
)
from smart_money.core.ids import deterministic_id

if TYPE_CHECKING:
    from smart_money.application.dashboard_query_result import (
        DashboardQueryResult,
    )


@dataclass(frozen=True, slots=True)
class DashboardMacroReadPage:
    """Deterministic page of canonical multi-subject dashboard responses."""

    items: tuple[DashboardMacroReadResponse, ...]
    total_count: int
    offset: int
    limit: int
    query: str
    schema_version: str = "dashboard_macro_read_index.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.items, tuple):
            raise TypeError("items must be a tuple")
        if not all(
            isinstance(item, DashboardMacroReadResponse) for item in self.items
        ):
            raise TypeError("items must contain dashboard read responses")
        for field_name in ("total_count", "offset", "limit"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field_name} must be an integer")
            if value < 0:
                raise ValueError(f"{field_name} must be non-negative")
        if self.limit == 0:
            raise ValueError("limit must be positive")
        if not isinstance(self.query, str):
            raise TypeError("query must be a string")
        if self.schema_version != "dashboard_macro_read_index.v1":
            raise ValueError("unsupported dashboard macro index schema_version")
        if len(self.items) > self.limit:
            raise ValueError("page contains more items than limit")
        if self.total_count < len(self.items):
            raise ValueError("total_count cannot be smaller than page size")

    @property
    def has_more(self) -> bool:
        return self.offset + len(self.items) < self.total_count

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "items": [item.canonical_dict() for item in self.items],
            "limit": self.limit,
            "offset": self.offset,
            "query": self.query,
            "schema_version": self.schema_version,
            "total_count": self.total_count,
        }

    @property
    def page_id(self) -> str:
        return deterministic_id(
            "dashboard_macro_read_index",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardMacroReadIndex:
    """In-memory canonical index for Token/Wallet dashboard responses."""

    responses: tuple[DashboardMacroReadResponse, ...]
    schema_version: str = "dashboard_macro_read_index.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.responses, tuple):
            raise TypeError("responses must be a tuple")
        if not all(
            isinstance(item, DashboardMacroReadResponse)
            for item in self.responses
        ):
            raise TypeError("responses must contain dashboard read responses")
        identifiers = [item.response_id for item in self.responses]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("responses contain duplicate response_id values")
        if self.schema_version != "dashboard_macro_read_index.v1":
            raise ValueError("unsupported dashboard macro index schema_version")

    @classmethod
    def from_responses(
        cls,
        responses: tuple[DashboardMacroReadResponse, ...] | list[DashboardMacroReadResponse],
    ) -> DashboardMacroReadIndex:
        return cls(responses=tuple(responses))

    def detail(self, response_id: str) -> DashboardSubjectDetail:
        """Return the canonical detail for one response identifier."""
        if not isinstance(response_id, str) or not response_id.strip():
            raise ValueError("response_id must be a non-empty string")
        matches = [
            item for item in self.responses if item.response_id == response_id
        ]
        if not matches:
            raise KeyError(f"unknown dashboard response_id: {response_id}")
        return DashboardSubjectDetail.from_response(matches[0])

    def detail_for_subject(
        self,
        subject_id: str,
        *,
        subject_kind: str | None = None,
    ) -> DashboardSubjectDetail:
        """Return a unique subject detail, failing closed on ambiguity."""
        if not isinstance(subject_id, str) or not subject_id.strip():
            raise ValueError("subject_id must be a non-empty string")
        if subject_kind is not None and not isinstance(subject_kind, str):
            raise TypeError("subject_kind must be a string or None")
        normalized_kind = (
            None if subject_kind is None else subject_kind.strip().upper()
        )
        matches = [
            item
            for item in self.responses
            if item.subject_id == subject_id
            and (
                normalized_kind is None
                or item.subject_kind == normalized_kind
            )
        ]
        if not matches:
            raise KeyError(f"unknown dashboard subject_id: {subject_id}")
        if len(matches) > 1:
            raise ValueError(
                f"ambiguous dashboard subject_id: {subject_id}"
            )
        return DashboardSubjectDetail.from_response(matches[0])

    def page_for_query(
        self,
        query: DashboardSubjectDetailQuery,
    ) -> DashboardMacroReadPage:
        if not isinstance(query, DashboardSubjectDetailQuery):
            raise TypeError("query must be a DashboardSubjectDetailQuery")
        return self.page(
            query=query.query,
            subject_kind=query.subject_kind,
            status=query.status,
            offset=query.offset,
            limit=query.limit,
        )

    def result_for_query(
        self,
        query: DashboardSubjectDetailQuery,
    ) -> DashboardQueryResult:
        from smart_money.application.dashboard_query_result import (
            DashboardQueryResult,
        )

        if not isinstance(query, DashboardSubjectDetailQuery):
            raise TypeError("query must be a DashboardSubjectDetailQuery")
        return DashboardQueryResult.from_page(
            query,
            self.page_for_query(query),
        )

    def page(
        self,
        *,
        query: str = "",
        subject_kind: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> DashboardMacroReadPage:
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        if subject_kind is not None and not isinstance(subject_kind, str):
            raise TypeError("subject_kind must be a string or None")
        if status is not None and not isinstance(status, str):
            raise TypeError("status must be a string or None")
        if isinstance(offset, bool) or not isinstance(offset, int):
            raise TypeError("offset must be an integer")
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be an integer")
        if offset < 0:
            raise ValueError("offset must be non-negative")
        if limit <= 0:
            raise ValueError("limit must be positive")

        normalized_query = query.strip().casefold()
        normalized_kind = None if subject_kind is None else subject_kind.strip().upper()
        normalized_status = None if status is None else status.strip().upper()
        filtered = [
            item
            for item in self.responses
            if (
                not normalized_query
                or normalized_query in item.subject_id.casefold()
                or normalized_query in item.model_id.casefold()
            )
            and (
                normalized_kind is None
                or item.subject_kind == normalized_kind
            )
            and (
                normalized_status is None
                or item.markdown.find(normalized_status) >= 0
            )
        ]
        ordered = tuple(
            sorted(
                filtered,
                key=lambda item: (
                    item.subject_kind,
                    item.subject_id,
                    item.response_id,
                ),
            )
        )
        return DashboardMacroReadPage(
            items=ordered[offset : offset + limit],
            total_count=len(ordered),
            offset=offset,
            limit=limit,
            query=query.strip(),
        )


__all__ = ["DashboardMacroReadIndex", "DashboardMacroReadPage"]
