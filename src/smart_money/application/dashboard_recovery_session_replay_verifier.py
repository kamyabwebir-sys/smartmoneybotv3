from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.dashboard_audit_recovery_gate import (
    DashboardAuditRecoveryReceipt,
)
from smart_money.application.dashboard_recovery_query_session import (
    DashboardRecoveryQuerySession,
    DashboardRecoveryQuerySessionReceipt,
)
from smart_money.application.dashboard_subject_detail_query import (
    DashboardSubjectDetailQuery,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class DashboardSessionReplayReceipt:
    expected_session_id: str
    actual_session_id: str
    matches: bool
    mismatches: tuple[str, ...] = ()
    schema_version: str = "dashboard_recovery_session_replay.v1"

    def __post_init__(self) -> None:
        for name in ("expected_session_id", "actual_session_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
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
        if self.schema_version != "dashboard_recovery_session_replay.v1":
            raise ValueError("unsupported dashboard session replay schema_version")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "actual_session_id": self.actual_session_id,
            "expected_session_id": self.expected_session_id,
            "matches": self.matches,
            "mismatches": list(self.mismatches),
            "schema_version": self.schema_version,
        }

    @property
    def verification_id(self) -> str:
        return deterministic_id(
            "dashboard_recovery_session_replay",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardRecoverySessionReplayVerifier:
    session: DashboardRecoveryQuerySession

    def __post_init__(self) -> None:
        if not isinstance(self.session, DashboardRecoveryQuerySession):
            raise TypeError("session must be a DashboardRecoveryQuerySession")

    def verify(
        self,
        recovery: DashboardAuditRecoveryReceipt,
        query: DashboardSubjectDetailQuery,
        expected: DashboardRecoveryQuerySessionReceipt,
    ) -> DashboardSessionReplayReceipt:
        if not isinstance(expected, DashboardRecoveryQuerySessionReceipt):
            raise TypeError(
                "expected must be a DashboardRecoveryQuerySessionReceipt"
            )
        _, _, actual = self.session.execute(recovery, query)
        mismatches = tuple(
            field
            for field in (
                "session_status",
                "recovery_receipt_id",
                "query_id",
                "query_receipt_id",
                "reason_code",
            )
            if getattr(expected, field) != getattr(actual, field)
        )
        return DashboardSessionReplayReceipt(
            expected_session_id=expected.session_id,
            actual_session_id=actual.session_id,
            matches=not mismatches,
            mismatches=mismatches,
        )


__all__ = [
    "DashboardRecoverySessionReplayVerifier",
    "DashboardSessionReplayReceipt",
]
