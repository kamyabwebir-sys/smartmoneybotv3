from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.dashboard_audit_head_anchor import (
    DashboardAuditHeadAnchor,
)
from smart_money.application.dashboard_query_audit_chain import (
    DashboardQueryAuditChain,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class DashboardAuditRecoveryReceipt:
    """Deterministic decision receipt for opening the dashboard audit gate."""

    decision: str
    reason_code: str
    anchor_id: str | None
    chain_id: str | None
    schema_version: str = "dashboard_audit_recovery.v1"

    def __post_init__(self) -> None:
        if self.decision not in {"READY", "BLOCKED"}:
            raise ValueError("decision must be READY or BLOCKED")
        if not isinstance(self.reason_code, str) or not self.reason_code.strip():
            raise ValueError("reason_code must be non-empty")
        for name in ("anchor_id", "chain_id"):
            value = getattr(self, name)
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                raise ValueError(f"{name} must be a non-empty string or None")
        if self.schema_version != "dashboard_audit_recovery.v1":
            raise ValueError("unsupported dashboard audit recovery schema_version")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "anchor_id": self.anchor_id,
            "chain_id": self.chain_id,
            "decision": self.decision,
            "reason_code": self.reason_code,
            "schema_version": self.schema_version,
        }

    @property
    def receipt_id(self) -> str:
        return deterministic_id(
            "dashboard_audit_recovery",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardAuditRecoveryGate:
    """Fail-closed gate for dashboard recovery."""

    def evaluate(
        self,
        chain: DashboardQueryAuditChain | None,
        anchor: DashboardAuditHeadAnchor | None,
    ) -> DashboardAuditRecoveryReceipt:
        if chain is None or anchor is None:
            return DashboardAuditRecoveryReceipt(
                decision="BLOCKED",
                reason_code="MISSING_CHAIN_OR_ANCHOR",
                anchor_id=None if anchor is None else anchor.anchor_id,
                chain_id=None if chain is None else chain.chain_id,
            )
        if not anchor.matches(chain):
            return DashboardAuditRecoveryReceipt(
                decision="BLOCKED",
                reason_code="CHAIN_HEAD_MISMATCH",
                anchor_id=anchor.anchor_id,
                chain_id=chain.chain_id,
            )
        return DashboardAuditRecoveryReceipt(
            decision="READY",
            reason_code="CHAIN_HEAD_VERIFIED",
            anchor_id=anchor.anchor_id,
            chain_id=chain.chain_id,
        )


__all__ = ["DashboardAuditRecoveryGate", "DashboardAuditRecoveryReceipt"]
