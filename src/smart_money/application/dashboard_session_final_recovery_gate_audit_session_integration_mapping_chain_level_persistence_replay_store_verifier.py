from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = (
    "dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_verification.v1"
)
_Receipt = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayReceipt
)


@runtime_checkable
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayReceiptStore(  # noqa: E501
    Protocol
):
    def get(self, verification_id: str) -> _Receipt | None: ...


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreAuditReceipt:  # noqa: E501
    expected_verification_id: str
    persisted_verification_id: str | None
    matches: bool
    mismatches: tuple[str, ...] = ()
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(
            self.expected_verification_id, str
        ) or not self.expected_verification_id.strip():
            raise ValueError("expected_verification_id must be a non-empty string")
        if self.persisted_verification_id is not None and (
            not isinstance(self.persisted_verification_id, str)
            or not self.persisted_verification_id.strip()
        ):
            raise ValueError("persisted_verification_id must be a non-empty string or None")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be a boolean")
        if not isinstance(self.mismatches, tuple) or not all(
            isinstance(item, str) and item.strip() for item in self.mismatches
        ):
            raise TypeError("mismatches must be a tuple of text values")
        if self.matches and self.mismatches:
            raise ValueError("matching store audit cannot contain mismatches")
        if not self.matches and not self.mismatches:
            raise ValueError("non-matching store audit requires mismatches")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported persistence replay store verification schema_version")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "expected_verification_id": self.expected_verification_id,
            "persisted_verification_id": self.persisted_verification_id,
            "matches": self.matches,
            "mismatches": list(self.mismatches),
            "schema_version": self.schema_version,
        }

    @property
    def audit_id(self) -> str:
        return deterministic_id(
            "dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_audit",
            self.canonical_dict(),
        )


_StoreReceipt = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreAuditReceipt
)


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreVerifier:  # noqa: E501
    receipt_store: (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayReceiptStore
    )

    def verify(
        self, expected: _Receipt
    ) -> _StoreReceipt:
        if not isinstance(expected, _Receipt):
            raise TypeError("expected must be a chain-level persistence replay receipt")
        persisted = self.receipt_store.get(expected.verification_id)
        if persisted is None:
            return _StoreReceipt(
                expected_verification_id=expected.verification_id,
                persisted_verification_id=None,
                matches=False,
                mismatches=("persisted_persistence_replay_receipt_missing",),
            )
        if not isinstance(persisted, _Receipt):
            raise TypeError("receipt_store returned an invalid persistence replay receipt")
        if persisted != expected:
            return _StoreReceipt(
                expected_verification_id=expected.verification_id,
                persisted_verification_id=persisted.verification_id,
                matches=False,
                mismatches=("persisted_persistence_replay_receipt_mismatch",),
            )
        return _StoreReceipt(
            expected_verification_id=expected.verification_id,
            persisted_verification_id=persisted.verification_id,
            matches=True,
        )


__all__ = [
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreAuditReceipt",
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreVerifier",
]
