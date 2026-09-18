from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_session_integration_mapper as mapping_model,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt:
    expected_mapping_id: str
    actual_mapping_id: str
    expected_full_audit_receipt_id: str
    actual_full_audit_receipt_id: str
    expected_full_audit_verification_id: str
    actual_full_audit_verification_id: str
    expected_binding_receipt_id: str
    actual_binding_receipt_id: str
    expected_chain_replay_verification_id: str | None
    actual_chain_replay_verification_id: str | None
    matches: bool
    mismatches: tuple[str, ...] = ()
    schema_version: str = (
        "dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay.v1"
    )

    def __post_init__(self) -> None:
        for name in (
            "expected_mapping_id",
            "actual_mapping_id",
            "expected_full_audit_receipt_id",
            "actual_full_audit_receipt_id",
            "expected_full_audit_verification_id",
            "actual_full_audit_verification_id",
            "expected_binding_receipt_id",
            "actual_binding_receipt_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")

        for name in (
            "expected_chain_replay_verification_id",
            "actual_chain_replay_verification_id",
        ):
            value = getattr(self, name)
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                raise ValueError(
                    f"{name} must be a non-empty string or None"
                )
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if not isinstance(self.mismatches, tuple) or not all(
            isinstance(item, str) and item.strip() for item in self.mismatches
        ):
            raise TypeError("mismatches must be a tuple of text values")
        if self.matches and self.mismatches:
            raise ValueError("matching replay cannot contain mismatches")
        if not self.matches and not self.mismatches:
            raise ValueError("non-matching replay requires mismatches")
        if (
            self.schema_version
            != "dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay.v1"
        ):
            raise ValueError(
                "unsupported session final recovery gate integration mapping replay schema_version"
            )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "actual_binding_receipt_id": self.actual_binding_receipt_id,
            "actual_chain_replay_verification_id": self.actual_chain_replay_verification_id,
            "actual_full_audit_receipt_id": self.actual_full_audit_receipt_id,
            "actual_full_audit_verification_id": self.actual_full_audit_verification_id,
            "actual_mapping_id": self.actual_mapping_id,
            "expected_binding_receipt_id": self.expected_binding_receipt_id,
            "expected_chain_replay_verification_id": self.expected_chain_replay_verification_id,
            "expected_full_audit_receipt_id": self.expected_full_audit_receipt_id,
            "expected_full_audit_verification_id": self.expected_full_audit_verification_id,
            "expected_mapping_id": self.expected_mapping_id,
            "matches": self.matches,
            "mismatches": list(self.mismatches),
            "schema_version": self.schema_version,
        }

    @property
    def verification_id(self) -> str:
        return deterministic_id(
            "dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier:
    """Replay verifier for persisted integration-mapping receipts."""

    def verify(
        self,
        expected: mapping_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
        actual: mapping_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
    ) -> DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt:
        if not isinstance(
            expected,
            mapping_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
        ):
            raise TypeError(
                "expected must be a "
                "DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt"
            )
        if not isinstance(
            actual,
            mapping_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
        ):
            raise TypeError(
                "actual must be a "
                "DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt"
            )

        mismatches = tuple(
            field
            for field in (
                "mapping_id",
                "chain_id",
                "chain_hash",
                "chain_entry_count",
                "chain_replay_verification_id",
                "full_audit_receipt_id",
                "full_audit_verification_id",
                "binding_receipt_id",
                "integration_session_id",
                "previous_integration_session_id",
                "decision",
                "reason_code",
            )
            if getattr(expected, field) != getattr(actual, field)
        )

        return DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt(
            expected_mapping_id=expected.mapping_id,
            actual_mapping_id=actual.mapping_id,
            expected_full_audit_receipt_id=expected.full_audit_receipt_id,
            actual_full_audit_receipt_id=actual.full_audit_receipt_id,
            expected_full_audit_verification_id=expected.full_audit_verification_id,
            actual_full_audit_verification_id=actual.full_audit_verification_id,
            expected_binding_receipt_id=expected.binding_receipt_id,
            actual_binding_receipt_id=actual.binding_receipt_id,
            expected_chain_replay_verification_id=expected.chain_replay_verification_id,
            actual_chain_replay_verification_id=actual.chain_replay_verification_id,
            matches=not mismatches,
            mismatches=mismatches,
        )


__all__ = [
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt",
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier",
]
