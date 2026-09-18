from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from smart_money.application.dashboard_session_final_recovery_gate_audit_recovery_replay_verifier import (
    DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "dashboard_session_final_recovery_gate_audit_recovery_replay_persistence.v1"


@runtime_checkable
class DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceiptStore(Protocol):
    def get(self, verification_id: str) -> (
        DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceipt | None
    ): ...


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditRecoveryReplayPersistenceAuditReceipt:
    expected_verification_id: str
    persisted_verification_id: str | None
    matches: bool
    mismatches: tuple[str, ...] = ()
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.expected_verification_id, str) or not self.expected_verification_id.strip():
            raise ValueError("expected_verification_id must be a non-empty string")
        if self.persisted_verification_id is not None and (
            not isinstance(self.persisted_verification_id, str)
            or not self.persisted_verification_id.strip()
        ):
            raise ValueError(
                "persisted_verification_id must be a non-empty string or None"
            )
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be a boolean")
        if not isinstance(self.mismatches, tuple) or not all(
            isinstance(value, str) and value.strip()
            for value in self.mismatches
        ):
            raise TypeError("mismatches must be a tuple of text values")
        if self.matches and self.mismatches:
            raise ValueError("matching persistence audit cannot contain mismatches")
        if not self.matches and not self.mismatches:
            raise ValueError("non-matching persistence audit requires mismatches")
        if (
            self.schema_version
            != _SCHEMA_VERSION
        ):
            raise ValueError(
                "unsupported final recovery gate audit recovery replay persistence schema_version"
            )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "expected_verification_id": self.expected_verification_id,
            "matches": self.matches,
            "persisted_verification_id": self.persisted_verification_id,
            "mismatches": list(self.mismatches),
            "schema_version": self.schema_version,
        }

    @property
    def audit_id(self) -> str:
        return deterministic_id(
            "dashboard_session_final_recovery_gate_audit_recovery_replay_persistence_audit",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditRecoveryReplayPersistenceVerifier:
    receipt_store: DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceiptStore

    def verify(
        self,
        expected: DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceipt,
    ) -> DashboardSessionFinalRecoveryGateAuditRecoveryReplayPersistenceAuditReceipt:
        if not isinstance(
            expected, DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceipt
        ):
            raise TypeError(
                "expected must be a DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceipt"
            )
        persisted = self.receipt_store.get(expected.verification_id)
        mismatches = ()
        if persisted is None:
            mismatches = ("persisted_replay_receipt_missing",)
            persisted_verification_id = None
        elif persisted != expected:
            mismatches = ("persisted_replay_receipt_mismatch",)
            persisted_verification_id = persisted.verification_id
        else:
            persisted_verification_id = persisted.verification_id

        return DashboardSessionFinalRecoveryGateAuditRecoveryReplayPersistenceAuditReceipt(
            expected_verification_id=expected.verification_id,
            persisted_verification_id=persisted_verification_id,
            matches=not mismatches,
            mismatches=mismatches,
        )


__all__ = [
    "DashboardSessionFinalRecoveryGateAuditRecoveryReplayPersistenceAuditReceipt",
    "DashboardSessionFinalRecoveryGateAuditRecoveryReplayPersistenceVerifier",
    "DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceiptStore",
]
