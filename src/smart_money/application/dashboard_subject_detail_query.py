from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class DashboardSubjectDetailQuery:
    """Canonical query contract for Token/Wallet dashboard details."""

    query: str = ""
    subject_kind: str | None = None
    status: str | None = None
    offset: int = 0
    limit: int = 50
    schema_version: str = "dashboard_subject_detail_query.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.query, str):
            raise TypeError("query must be a string")
        object.__setattr__(self, "query", self.query.strip())
        for field_name in ("subject_kind", "status"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string or None")
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    value.strip().upper(),
                )
        for field_name in ("offset", "limit"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field_name} must be an integer")
        if self.offset < 0:
            raise ValueError("offset must be non-negative")
        if self.limit <= 0:
            raise ValueError("limit must be positive")
        if self.schema_version != "dashboard_subject_detail_query.v1":
            raise ValueError(
                "unsupported dashboard subject detail query schema_version"
            )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "limit": self.limit,
            "offset": self.offset,
            "query": self.query,
            "schema_version": self.schema_version,
            "status": self.status,
            "subject_kind": self.subject_kind,
        }

    @property
    def query_id(self) -> str:
        return deterministic_id(
            "dashboard_subject_detail_query",
            self.canonical_dict(),
        )


__all__ = ["DashboardSubjectDetailQuery"]
