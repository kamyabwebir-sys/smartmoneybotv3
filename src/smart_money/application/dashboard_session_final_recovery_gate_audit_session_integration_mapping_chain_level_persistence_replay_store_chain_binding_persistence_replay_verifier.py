from __future__ import annotations

# ruff: noqa: E501
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_persistence_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceAuditReceipt,
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = (
    "dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_persistence_replay.v1"
)


@runtime_checkable
class _AuditReceiptStore(Protocol):
    def get(self, audit_id: str) -> DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceAuditReceipt | None: ...

    def iter_receipts(self): ...


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceReplayAuditReceipt:
    expected_audit_id: str
    generated_audit_id: str
    persisted_audit_id: str | None
    matches: bool
    mismatches: tuple[str, ...] = ()
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (
            ("expected_audit_id", self.expected_audit_id),
            ("generated_audit_id", self.generated_audit_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
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
            raise ValueError("matching replay audit cannot contain mismatches")
        if not self.matches and not self.mismatches:
            raise ValueError("non-matching replay audit requires mismatches")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported chain binding replay schema_version")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "expected_audit_id": self.expected_audit_id,
            "generated_audit_id": self.generated_audit_id,
            "persisted_audit_id": self.persisted_audit_id,
            "matches": self.matches,
            "mismatches": list(self.mismatches),
            "schema_version": self.schema_version,
        }

    @property
    def audit_id(self) -> str:
        return deterministic_id(
            "dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_persistence_replay_audit",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceReplayVerifier:
    receipt_store: _AuditReceiptStore

    def verify(self, expected: DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingReceipt) -> DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceReplayAuditReceipt:
        if not isinstance(expected, DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingReceipt):
            raise TypeError("expected must be a chain binding receipt")
        persisted = next(
            (
                item
                for item in self.receipt_store.iter_receipts()
                if item.expected_audit_id == expected.audit_id
            ),
            None,
        )
        generated = (
            None
            if persisted is None
            else DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceAuditReceipt(
                expected_audit_id=persisted.expected_audit_id,
                persisted_audit_id=persisted.persisted_audit_id,
                matches=persisted.matches,
                mismatches=persisted.mismatches,
                schema_version=persisted.schema_version,
            )
        )
        if persisted is None:
            return _AuditReceipt(
                expected_audit_id=expected.audit_id,
                generated_audit_id=expected.audit_id,
                persisted_audit_id=None,
                matches=False,
                mismatches=("persisted_chain_binding_replay_audit_missing",),
            )
        if generated is None or persisted != generated:
            return _AuditReceipt(
                expected_audit_id=expected.audit_id,
                generated_audit_id=generated.audit_id,
                persisted_audit_id=persisted.audit_id,
                matches=False,
                mismatches=("persisted_chain_binding_replay_audit_mismatch",),
            )
        return _AuditReceipt(
            expected_audit_id=expected.audit_id,
            generated_audit_id=generated.audit_id,
            persisted_audit_id=persisted.audit_id,
            matches=True,
        )


_AuditReceipt = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceReplayAuditReceipt


@dataclass(frozen=True, slots=True)
class _ExpectedLookupStore:
    receipt: DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceAuditReceipt | None

    def get(self, audit_id: str):
        if self.receipt is not None and self.receipt.expected_audit_id == audit_id:
            return self.receipt
        return None

__all__ = [
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceReplayAuditReceipt",
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceReplayVerifier",
]
