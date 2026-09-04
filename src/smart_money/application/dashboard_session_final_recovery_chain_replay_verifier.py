from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.dashboard_session_final_recovery_audit_chain import (
    DashboardSessionFinalRecoveryAuditChain,
)
from smart_money.application.dashboard_session_final_recovery_audit_chain_replay_verifier import (
    DashboardSessionFinalRecoveryAuditChainReplayReceipt,
)
from smart_money.application.dashboard_session_final_recovery_chain_gate import (
    DashboardSessionFinalRecoveryChainGate,
    DashboardSessionFinalRecoveryChainReceipt,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryChainReplayReceipt:
    expected_receipt_id: str
    actual_receipt_id: str
    matches: bool
    mismatches: tuple[str, ...] = ()
    schema_version: str = (
        "dashboard_session_final_recovery_chain_replay.v1"
    )

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
        if (
            self.schema_version
            != "dashboard_session_final_recovery_chain_replay.v1"
        ):
            raise ValueError(
                "unsupported final recovery chain replay schema_version"
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
            "dashboard_session_final_recovery_chain_replay",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryChainReplayVerifier:
    gate: DashboardSessionFinalRecoveryChainGate = (
        DashboardSessionFinalRecoveryChainGate()
    )

    def verify(
        self,
        expected: DashboardSessionFinalRecoveryChainReceipt,
        chain: DashboardSessionFinalRecoveryAuditChain | None,
        replay: DashboardSessionFinalRecoveryAuditChainReplayReceipt | None,
        persisted_replay: (
            DashboardSessionFinalRecoveryAuditChainReplayReceipt | None
        ),
    ) -> DashboardSessionFinalRecoveryChainReplayReceipt:
        if not isinstance(
            expected, DashboardSessionFinalRecoveryChainReceipt
        ):
            raise TypeError(
                "expected must be a DashboardSessionFinalRecoveryChainReceipt"
            )
        actual = self.gate.evaluate(chain, replay, persisted_replay)
        mismatches = tuple(
            field
            for field in (
                "decision",
                "reason_code",
                "chain_id",
                "replay_verification_id",
            )
            if getattr(expected, field) != getattr(actual, field)
        )
        return DashboardSessionFinalRecoveryChainReplayReceipt(
            expected_receipt_id=expected.receipt_id,
            actual_receipt_id=actual.receipt_id,
            matches=not mismatches,
            mismatches=mismatches,
        )


__all__ = [
    "DashboardSessionFinalRecoveryChainReplayReceipt",
    "DashboardSessionFinalRecoveryChainReplayVerifier",
]
