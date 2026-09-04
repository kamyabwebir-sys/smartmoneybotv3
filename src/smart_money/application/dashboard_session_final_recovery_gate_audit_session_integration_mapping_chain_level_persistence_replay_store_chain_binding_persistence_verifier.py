from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = (
    "dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_persistence.v1"
)
_Receipt = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingReceipt
)


@runtime_checkable
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingReceiptStore(  # noqa: E501
    Protocol
):
    def get(self, audit_id: str) -> _Receipt | None: ...


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceAuditReceipt:  # noqa: E501
    expected_audit_id: str
    persisted_audit_id: str | None
    matches: bool
    mismatches: tuple[str, ...] = ()
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.expected_audit_id, str) or not self.expected_audit_id.strip():
            raise ValueError("expected_audit_id must be a non-empty string")
        if self.persisted_audit_id is not None and (
            not isinstance(self.persisted_audit_id, str)
            or not self.persisted_audit_id.strip()
        ):
            raise ValueError("persisted_audit_id must be a non-empty string or None")
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
            raise ValueError("unsupported chain binding persistence schema_version")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "expected_audit_id": self.expected_audit_id,
            "persisted_audit_id": self.persisted_audit_id,
            "matches": self.matches,
            "mismatches": list(self.mismatches),
            "schema_version": self.schema_version,
        }

    @property
    def audit_id(self) -> str:
        return deterministic_id(
            "dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_persistence_audit",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceVerifier:  # noqa: E501
    receipt_store: (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingReceiptStore
    )

    def verify(self, expected: _Receipt) -> (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceAuditReceipt
    ):
        if not isinstance(expected, _Receipt):
            raise TypeError("expected must be a chain binding receipt")
        persisted = self.receipt_store.get(expected.audit_id)
        if persisted is None:
            return _AuditReceipt(
                expected_audit_id=expected.audit_id,
                persisted_audit_id=None,
                matches=False,
                mismatches=("persisted_chain_binding_receipt_missing",),
            )
        if not isinstance(persisted, _Receipt):
            raise TypeError("receipt_store returned an invalid chain binding receipt")
        if persisted != expected:
            return _AuditReceipt(
                expected_audit_id=expected.audit_id,
                persisted_audit_id=persisted.audit_id,
                matches=False,
                mismatches=("persisted_chain_binding_receipt_mismatch",),
            )
        return _AuditReceipt(
            expected_audit_id=expected.audit_id,
            persisted_audit_id=persisted.audit_id,
            matches=True,
        )


_AuditReceipt = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceAuditReceipt
)

__all__ = [
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceAuditReceipt",
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceVerifier",
]
