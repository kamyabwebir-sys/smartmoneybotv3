from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_verifier import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = (
    "dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_persistence.v1"
)


@runtime_checkable
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceiptStore(
    Protocol
):
    def get(
        self, verification_id: str
    ) -> DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt | None: ...


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceAuditReceipt:
    expected_verification_id: str
    persisted_verification_id: str | None
    matches: bool
    mismatches: tuple[str, ...] = ()
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (
            not isinstance(self.expected_verification_id, str)
            or not self.expected_verification_id.strip()
        ):
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
            isinstance(item, str) and item.strip() for item in self.mismatches
        ):
            raise TypeError("mismatches must be a tuple of text values")
        if self.matches and self.mismatches:
            raise ValueError("matching persistence audit cannot contain mismatches")
        if not self.matches and not self.mismatches:
            raise ValueError("non-matching persistence audit requires mismatches")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError(
                "unsupported session integration mapping replay persistence schema_version"
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
            "dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_persistence_audit",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceVerifier:
    receipt_store: (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceiptStore
    )

    def verify(
        self,
        expected: DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt,
    ) -> DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceAuditReceipt:
        if not isinstance(
            expected,
            DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt,
        ):
            raise TypeError(
                "expected must be a DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt"
            )

        persisted = self.receipt_store.get(expected.verification_id)
        if persisted is None and not expected.matches:
            canonical_match = (
                DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt(
                    expected_mapping_id=expected.expected_mapping_id,
                    actual_mapping_id=expected.expected_mapping_id,
                    expected_full_audit_receipt_id=expected.expected_full_audit_receipt_id,
                    actual_full_audit_receipt_id=expected.expected_full_audit_receipt_id,
                    expected_full_audit_verification_id=expected.expected_full_audit_verification_id,
                    actual_full_audit_verification_id=expected.expected_full_audit_verification_id,
                    expected_binding_receipt_id=expected.expected_binding_receipt_id,
                    actual_binding_receipt_id=expected.expected_binding_receipt_id,
                    expected_chain_replay_verification_id=expected.expected_chain_replay_verification_id,
                    actual_chain_replay_verification_id=expected.expected_chain_replay_verification_id,
                    matches=True,
                )
            )
            persisted = self.receipt_store.get(canonical_match.verification_id)
        if persisted is None:
            return DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceAuditReceipt(
                expected_verification_id=expected.verification_id,
                persisted_verification_id=None,
                matches=False,
                mismatches=("persisted_replay_receipt_missing",),
            )
        if persisted != expected:
            return DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceAuditReceipt(
                expected_verification_id=expected.verification_id,
                persisted_verification_id=persisted.verification_id,
                matches=False,
                mismatches=("persisted_replay_receipt_mismatch",),
            )
        return DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceAuditReceipt(
            expected_verification_id=expected.verification_id,
            persisted_verification_id=persisted.verification_id,
            matches=True,
        )


__all__ = [
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceAuditReceipt",
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceVerifier",
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceiptStore",
]
