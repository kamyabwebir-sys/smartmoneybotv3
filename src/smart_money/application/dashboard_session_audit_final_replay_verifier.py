from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.dashboard_session_audit_chain import (
    DashboardSessionAuditChain,
)
from smart_money.application.dashboard_session_audit_finalizer import (
    DashboardSessionAuditChainFinalizer,
    DashboardSessionAuditFinalReceipt,
)
from smart_money.application.dashboard_session_audit_head_anchor import (
    DashboardSessionAuditHeadAnchor,
)
from smart_money.application.dashboard_session_recovery_gate import (
    DashboardSessionRecoveryReceipt,
)
from smart_money.application.dashboard_session_recovery_replay_verifier import (
    DashboardSessionRecoveryReplayReceipt,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class DashboardSessionAuditFinalReplayReceipt:
    expected_receipt_id: str
    actual_receipt_id: str
    matches: bool
    mismatches: tuple[str, ...] = ()
    schema_version: str = "dashboard_session_audit_final_replay.v1"

    def __post_init__(self) -> None:
        for name in ("expected_receipt_id", "actual_receipt_id"):
            if not isinstance(getattr(self, name), str) or not getattr(
                self, name
            ).strip():
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
        if self.schema_version != "dashboard_session_audit_final_replay.v1":
            raise ValueError(
                "unsupported session audit final replay schema_version"
            )

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
            "dashboard_session_audit_final_replay",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardSessionAuditFinalReplayVerifier:
    finalizer: DashboardSessionAuditChainFinalizer = (
        DashboardSessionAuditChainFinalizer()
    )

    def verify(
        self,
        expected: DashboardSessionAuditFinalReceipt,
        chain: DashboardSessionAuditChain | None,
        anchor: DashboardSessionAuditHeadAnchor | None,
        recovery: DashboardSessionRecoveryReceipt,
        replay: DashboardSessionRecoveryReplayReceipt,
    ) -> DashboardSessionAuditFinalReplayReceipt:
        if not isinstance(expected, DashboardSessionAuditFinalReceipt):
            raise TypeError(
                "expected must be a DashboardSessionAuditFinalReceipt"
            )
        actual = self.finalizer.finalize(chain, anchor, recovery, replay)
        mismatches = tuple(
            field
            for field in (
                "chain_id",
                "chain_hash",
                "head_anchor_id",
                "recovery_receipt_id",
                "recovery_replay_verification_id",
                "entry_count",
                "decision",
                "reason_code",
            )
            if getattr(expected, field) != getattr(actual, field)
        )
        return DashboardSessionAuditFinalReplayReceipt(
            expected_receipt_id=expected.receipt_id,
            actual_receipt_id=actual.receipt_id,
            matches=not mismatches,
            mismatches=mismatches,
        )


__all__ = [
    "DashboardSessionAuditFinalReplayReceipt",
    "DashboardSessionAuditFinalReplayVerifier",
]
