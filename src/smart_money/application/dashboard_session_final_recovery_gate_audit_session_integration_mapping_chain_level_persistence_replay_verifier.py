from __future__ import annotations

from dataclasses import dataclass

from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceAuditReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = (
    "dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay.v1"
)
_AuditReceipt = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceAuditReceipt
)


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayReceipt:  # noqa: E501
    expected_persistence_audit_id: str
    actual_persistence_audit_id: str
    matches: bool
    mismatches: tuple[str, ...] = ()
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for value, name in (
            (self.expected_persistence_audit_id, "expected_persistence_audit_id"),
            (self.actual_persistence_audit_id, "actual_persistence_audit_id"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be a boolean")
        if not isinstance(self.mismatches, tuple) or not all(
            isinstance(item, str) and item.strip() for item in self.mismatches
        ):
            raise TypeError("mismatches must be a tuple of text values")
        if self.matches and self.mismatches:
            raise ValueError("matching replay cannot contain mismatches")
        if not self.matches and not self.mismatches:
            raise ValueError("non-matching replay requires mismatches")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported chain-level persistence replay schema_version")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "actual_persistence_audit_id": self.actual_persistence_audit_id,
            "expected_persistence_audit_id": self.expected_persistence_audit_id,
            "matches": self.matches,
            "mismatches": list(self.mismatches),
            "schema_version": self.schema_version,
        }

    @property
    def verification_id(self) -> str:
        return deterministic_id(
            "dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay",
            self.canonical_dict(),
        )


_ReplayReceipt = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayReceipt
)


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayVerifier:  # noqa: E501
    def verify(
        self,
        expected: _AuditReceipt,
        actual: _AuditReceipt,
    ) -> _ReplayReceipt:
        for value, name in ((expected, "expected"), (actual, "actual")):
            if not isinstance(
                value,
                _AuditReceipt,
            ):
                raise TypeError(f"{name} must be a chain-level persistence audit receipt")

        mismatches = ()
        if expected.audit_id != actual.audit_id:
            mismatches = ("persistence_audit_id_mismatch",)
        elif expected != actual:
            mismatches = ("persistence_audit_receipt_mismatch",)

        return (
            DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayReceipt(
                expected_persistence_audit_id=expected.audit_id,
                actual_persistence_audit_id=actual.audit_id,
                matches=not mismatches,
                mismatches=mismatches,
            )
        )


__all__ = [
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayReceipt",
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayVerifier",
]
