from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.dashboard_query_audit_receipt import (
    DashboardQueryAuditReceipt,
)
from smart_money.application.dashboard_query_endpoint import (
    DashboardQueryEndpoint,
)
from smart_money.application.dashboard_subject_detail_query import (
    DashboardSubjectDetailQuery,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class DashboardQueryReplayReceipt:
    """Deterministic comparison receipt for a replayed dashboard query."""

    query_id: str | None
    expected_receipt_id: str
    actual_receipt_id: str
    matches: bool
    mismatches: tuple[str, ...] = ()
    schema_version: str = "dashboard_query_replay.v1"

    def __post_init__(self) -> None:
        for field_name in (
            "expected_receipt_id",
            "actual_receipt_id",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if self.query_id is not None and not isinstance(self.query_id, str):
            raise TypeError("query_id must be a string or None")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be a boolean")
        if not isinstance(self.mismatches, tuple) or not all(
            isinstance(item, str) and item.strip()
            for item in self.mismatches
        ):
            raise TypeError("mismatches must be a tuple of text values")
        if self.matches and self.mismatches:
            raise ValueError("matching replay cannot contain mismatches")
        if not self.matches and not self.mismatches:
            raise ValueError("non-matching replay requires mismatches")
        if self.schema_version != "dashboard_query_replay.v1":
            raise ValueError("unsupported dashboard query replay schema_version")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "actual_receipt_id": self.actual_receipt_id,
            "expected_receipt_id": self.expected_receipt_id,
            "matches": self.matches,
            "mismatches": list(self.mismatches),
            "query_id": self.query_id,
            "schema_version": self.schema_version,
        }

    @property
    def verification_id(self) -> str:
        return deterministic_id(
            "dashboard_query_replay",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardQueryReplayVerifier:
    """Replay verifier that compares current execution with a stored receipt."""

    endpoint: DashboardQueryEndpoint

    def __post_init__(self) -> None:
        if not isinstance(self.endpoint, DashboardQueryEndpoint):
            raise TypeError("endpoint must be a DashboardQueryEndpoint")

    def verify(
        self,
        query: DashboardSubjectDetailQuery,
        expected: DashboardQueryAuditReceipt,
    ) -> DashboardQueryReplayReceipt:
        if not isinstance(query, DashboardSubjectDetailQuery):
            raise TypeError("query must be a DashboardSubjectDetailQuery")
        if not isinstance(expected, DashboardQueryAuditReceipt):
            raise TypeError("expected must be a DashboardQueryAuditReceipt")
        _, actual = self.endpoint.execute_with_receipt(query)
        mismatches = tuple(
            field_name
            for field_name in (
                "query_id",
                "status",
                "artifact_id",
                "artifact_kind",
                "output_hash",
                "item_count",
                "schema_versions",
                "error_code",
            )
            if getattr(expected, field_name) != getattr(actual, field_name)
        )
        return DashboardQueryReplayReceipt(
            query_id=query.query_id,
            expected_receipt_id=expected.receipt_id,
            actual_receipt_id=actual.receipt_id,
            matches=not mismatches,
            mismatches=mismatches,
        )


__all__ = ["DashboardQueryReplayReceipt", "DashboardQueryReplayVerifier"]
