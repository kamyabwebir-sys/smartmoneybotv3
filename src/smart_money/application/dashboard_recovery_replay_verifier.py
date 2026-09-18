from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.dashboard_audit_head_anchor import (
    DashboardAuditHeadAnchor,
)
from smart_money.application.dashboard_audit_recovery_gate import (
    DashboardAuditRecoveryGate,
    DashboardAuditRecoveryReceipt,
)
from smart_money.application.dashboard_query_audit_chain import (
    DashboardQueryAuditChain,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class DashboardRecoveryReplayReceipt:
    """Deterministic replay comparison for a recovery gate receipt."""

    expected_receipt_id: str
    actual_receipt_id: str
    matches: bool
    mismatches: tuple[str, ...] = ()
    schema_version: str = "dashboard_recovery_replay.v1"

    def __post_init__(self) -> None:
        for name in ("expected_receipt_id", "actual_receipt_id"):
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
        if self.schema_version != "dashboard_recovery_replay.v1":
            raise ValueError("unsupported dashboard recovery replay schema_version")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "actual_receipt_id": self.actual_receipt_id,
            "expected_receipt_id": self.expected_receipt_id,
            "matches": self.matches,
            "mismatches": list(self.mismatches),
            "schema_version": self.schema_version,
        }

    @property
    def verification_id(self) -> str:
        return deterministic_id(
            "dashboard_recovery_replay",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardRecoveryReplayVerifier:
    gate: DashboardAuditRecoveryGate = DashboardAuditRecoveryGate()

    def verify(
        self,
        chain: DashboardQueryAuditChain | None,
        anchor: DashboardAuditHeadAnchor | None,
        expected: DashboardAuditRecoveryReceipt,
    ) -> DashboardRecoveryReplayReceipt:
        if not isinstance(expected, DashboardAuditRecoveryReceipt):
            raise TypeError("expected must be a DashboardAuditRecoveryReceipt")
        actual = self.gate.evaluate(chain, anchor)
        mismatches = tuple(
            field
            for field in ("decision", "reason_code", "anchor_id", "chain_id")
            if getattr(expected, field) != getattr(actual, field)
        )
        return DashboardRecoveryReplayReceipt(
            expected_receipt_id=expected.receipt_id,
            actual_receipt_id=actual.receipt_id,
            matches=not mismatches,
            mismatches=mismatches,
        )


__all__ = ["DashboardRecoveryReplayReceipt", "DashboardRecoveryReplayVerifier"]
