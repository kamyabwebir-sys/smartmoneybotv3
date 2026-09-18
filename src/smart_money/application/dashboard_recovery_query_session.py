from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.dashboard_audit_recovery_gate import (
    DashboardAuditRecoveryReceipt,
)
from smart_money.application.dashboard_query_audit_receipt import (
    DashboardQueryAuditReceipt,
)
from smart_money.application.dashboard_query_endpoint import (
    DashboardQueryEndpoint,
)
from smart_money.application.dashboard_query_error import DashboardQueryError
from smart_money.application.dashboard_query_result import DashboardQueryResult
from smart_money.application.dashboard_subject_detail_query import (
    DashboardSubjectDetailQuery,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class DashboardRecoveryQuerySessionReceipt:
    """Canonical receipt for a recovery-gated dashboard query session."""

    session_status: str
    recovery_receipt_id: str
    query_id: str | None
    query_receipt_id: str | None
    reason_code: str
    schema_version: str = "dashboard_recovery_query_session.v1"

    def __post_init__(self) -> None:
        if self.session_status not in {"EXECUTED", "BLOCKED"}:
            raise ValueError("session_status must be EXECUTED or BLOCKED")
        for name in ("recovery_receipt_id", "reason_code"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        for name in ("query_id", "query_receipt_id"):
            value = getattr(self, name)
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                raise ValueError(f"{name} must be a non-empty string or None")
        if self.session_status == "EXECUTED" and (
            self.query_id is None or self.query_receipt_id is None
        ):
            raise ValueError("executed session requires query identifiers")
        if self.session_status == "BLOCKED" and self.query_receipt_id is not None:
            raise ValueError("blocked session cannot have query receipt")
        if self.schema_version != "dashboard_recovery_query_session.v1":
            raise ValueError("unsupported dashboard recovery session schema_version")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "query_receipt_id": self.query_receipt_id,
            "reason_code": self.reason_code,
            "recovery_receipt_id": self.recovery_receipt_id,
            "schema_version": self.schema_version,
            "session_status": self.session_status,
        }

    @property
    def session_id(self) -> str:
        return deterministic_id(
            "dashboard_recovery_query_session",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardRecoveryQuerySession:
    """Runs dashboard queries only after a READY recovery decision."""

    endpoint: DashboardQueryEndpoint

    def __post_init__(self) -> None:
        if not isinstance(self.endpoint, DashboardQueryEndpoint):
            raise TypeError("endpoint must be a DashboardQueryEndpoint")

    def execute(
        self,
        recovery: DashboardAuditRecoveryReceipt,
        query: DashboardSubjectDetailQuery,
    ) -> tuple[
        DashboardQueryResult | DashboardQueryError | None,
        DashboardQueryAuditReceipt | None,
        DashboardRecoveryQuerySessionReceipt,
    ]:
        if not isinstance(recovery, DashboardAuditRecoveryReceipt):
            raise TypeError("recovery must be a DashboardAuditRecoveryReceipt")
        if not isinstance(query, DashboardSubjectDetailQuery):
            raise TypeError("query must be a DashboardSubjectDetailQuery")
        if recovery.decision != "READY":
            receipt = DashboardRecoveryQuerySessionReceipt(
                session_status="BLOCKED",
                recovery_receipt_id=recovery.receipt_id,
                query_id=query.query_id,
                query_receipt_id=None,
                reason_code="RECOVERY_GATE_BLOCKED",
            )
            return None, None, receipt
        outcome, query_receipt = self.endpoint.execute_with_receipt(query)
        session_receipt = DashboardRecoveryQuerySessionReceipt(
            session_status="EXECUTED",
            recovery_receipt_id=recovery.receipt_id,
            query_id=query.query_id,
            query_receipt_id=query_receipt.receipt_id,
            reason_code="RECOVERY_GATE_READY",
        )
        return outcome, query_receipt, session_receipt


__all__ = [
    "DashboardRecoveryQuerySession",
    "DashboardRecoveryQuerySessionReceipt",
]
