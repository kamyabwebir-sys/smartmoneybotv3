from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from smart_money.application.dashboard_session_final_recovery_gate_audit_chain import (
    DashboardSessionFinalRecoveryGateAuditChain,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreAuditReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = (
    "dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding.v1"
)
_AuditReceipt = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreAuditReceipt
)


@runtime_checkable
class _EntryLike(Protocol):
    entry_id: str
    entry_kind: str


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingReceipt:  # noqa: E501
    chain_id: str
    chain_hash: str
    chain_entry_count: int
    expected_store_audit_id: str
    chain_entry_present: bool
    matches: bool
    mismatches: tuple[str, ...] = ()
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for value, name in (
            (self.chain_id, "chain_id"),
            (self.chain_hash, "chain_hash"),
            (self.expected_store_audit_id, "expected_store_audit_id"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.chain_entry_count, int) or isinstance(
            self.chain_entry_count, bool
        ) or self.chain_entry_count < 0:
            raise ValueError("chain_entry_count must be a non-negative integer")
        if not isinstance(self.chain_entry_present, bool):
            raise TypeError("chain_entry_present must be a boolean")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be a boolean")
        if not isinstance(self.mismatches, tuple) or not all(
            isinstance(item, str) and item.strip() for item in self.mismatches
        ):
            raise TypeError("mismatches must be a tuple of text values")
        if self.matches and self.mismatches:
            raise ValueError("matching chain binding cannot contain mismatches")
        if not self.matches and not self.mismatches:
            raise ValueError("non-matching chain binding requires mismatches")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported chain binding schema_version")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "chain_entry_count": self.chain_entry_count,
            "chain_entry_present": self.chain_entry_present,
            "chain_hash": self.chain_hash,
            "chain_id": self.chain_id,
            "expected_store_audit_id": self.expected_store_audit_id,
            "matches": self.matches,
            "mismatches": list(self.mismatches),
            "schema_version": self.schema_version,
        }

    @property
    def audit_id(self) -> str:
        return deterministic_id(
            "dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingVerifier:  # noqa: E501
    def verify(
        self,
        chain: DashboardSessionFinalRecoveryGateAuditChain,
        store_audit: _AuditReceipt,
    ) -> DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingReceipt:  # noqa: E501
        if not isinstance(chain, DashboardSessionFinalRecoveryGateAuditChain):
            raise TypeError("chain must be a DashboardSessionFinalRecoveryGateAuditChain")
        if not isinstance(store_audit, _AuditReceipt):
            raise TypeError("store_audit must be a persistence replay store audit receipt")

        mismatches: tuple[str, ...] = ()
        if not store_audit.matches:
            mismatches += ("store_audit_not_matching",)
        entry_present = any(
            isinstance(entry, _EntryLike)
            and entry.entry_id == store_audit.audit_id
            and entry.entry_kind == "persistence_replay_store_audit"
            for entry in chain.entries
        )
        if not entry_present:
            mismatches += ("persistence_replay_store_audit_missing_in_chain",)
        matches = not mismatches
        return (
            DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingReceipt(
                chain_id=chain.chain_id,
                chain_hash=chain.chain_hash,
                chain_entry_count=len(chain.entries),
                expected_store_audit_id=store_audit.audit_id,
                chain_entry_present=entry_present,
                matches=matches,
                mismatches=mismatches,
            )
        )


__all__ = [
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingReceipt",
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingVerifier",
]
