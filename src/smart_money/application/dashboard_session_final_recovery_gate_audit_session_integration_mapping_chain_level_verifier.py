from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from smart_money.application.dashboard_session_final_recovery_gate_audit_chain import (
    DashboardSessionFinalRecoveryGateAuditChain,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapper import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt as DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReceipt,  # noqa: E501
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_binding_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainBindingReceipt,
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainBindingVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceAuditReceipt,
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_persistence_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceAuditReceipt,
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = (
    "dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level.v1"
)

_MappingReceipt = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReceipt
)
_BindingReceipt = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainBindingReceipt
)
_ChainPersistenceAuditReceipt = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceAuditReceipt
)
_ReplayPersistenceAuditReceipt = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceAuditReceipt
)
_ReplayReceipt = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt
_BindingVerifier = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainBindingVerifier
)
_ChainPersistenceVerifier = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceVerifier
)
_ReplayPersistenceVerifier = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceVerifier
)


@runtime_checkable
class _ChainLike(Protocol):
    chain_id: str
    chain_hash: str
    entries: tuple[object, ...]


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelAuditReceipt:
    chain_id: str
    chain_hash: str
    chain_entry_count: int
    mapping_id: str
    mapping_replay_verification_id: str
    mapping_chain_binding: _BindingReceipt
    mapping_chain_persistence: _ChainPersistenceAuditReceipt
    mapping_replay_persistence: _ReplayPersistenceAuditReceipt
    chain_entry_mapping_presence: bool
    chain_entry_mapping_replay_presence: bool
    matches: bool
    mismatches: tuple[str, ...] = ()
    decision: str = "BLOCKED"
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for value, name in (
            (self.chain_id, "chain_id"),
            (self.chain_hash, "chain_hash"),
            (self.mapping_id, "mapping_id"),
            (self.mapping_replay_verification_id, "mapping_replay_verification_id"),
            (self.decision, "decision"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.decision not in {"READY", "BLOCKED"}:
            raise ValueError("decision must be READY or BLOCKED")
        if (
            not isinstance(self.chain_entry_count, int)
            or isinstance(self.chain_entry_count, bool)
            or self.chain_entry_count < 0
        ):
            raise ValueError("chain_entry_count must be a non-negative integer")
        if not isinstance(self.chain_entry_mapping_presence, bool):
            raise TypeError("chain_entry_mapping_presence must be a boolean")
        if not isinstance(self.chain_entry_mapping_replay_presence, bool):
            raise TypeError("chain_entry_mapping_replay_presence must be a boolean")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be a boolean")
        if not isinstance(self.mismatches, tuple) or not all(
            isinstance(item, str) and item.strip() for item in self.mismatches
        ):
            raise TypeError("mismatches must be a tuple of text values")
        if self.matches and self.mismatches:
            raise ValueError("matching receipt cannot contain mismatches")
        if not self.matches and not self.mismatches:
            raise ValueError("non-matching receipt requires mismatches")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported session integration mapping chain-level schema_version")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "chain_entry_count": self.chain_entry_count,
            "chain_hash": self.chain_hash,
            "chain_id": self.chain_id,
            "chain_entry_mapping_presence": self.chain_entry_mapping_presence,
            "chain_entry_mapping_replay_presence": self.chain_entry_mapping_replay_presence,
            "mapping_chain_binding_verification": self.mapping_chain_binding.chain_id
            == self.chain_id,
            "mapping_chain_persistence_verification": self.mapping_chain_persistence.matches,
            "mapping_id": self.mapping_id,
            "mapping_replay_persistence_verification": self.mapping_replay_persistence.matches,
            "mapping_replay_verification_id": self.mapping_replay_verification_id,
            "mismatches": list(self.mismatches),
            "matches": self.matches,
            "decision": self.decision,
            "schema_version": self.schema_version,
        }

    @property
    def audit_id(self) -> str:
        return deterministic_id(
            "dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelVerifier:
    chain_binding_verifier: _BindingVerifier = field(default=None)
    chain_persistence_verifier: _ChainPersistenceVerifier = field(default=None)
    replay_persistence_verifier: _ReplayPersistenceVerifier = field(default=None)

    def __post_init__(self) -> None:
        if self.chain_binding_verifier is None:
            raise TypeError("chain_binding_verifier is required")
        if self.chain_persistence_verifier is None:
            raise TypeError("chain_persistence_verifier is required")
        if self.replay_persistence_verifier is None:
            raise TypeError("replay_persistence_verifier is required")

    def verify(
        self,
        chain: DashboardSessionFinalRecoveryGateAuditChain,
        mapping: _MappingReceipt,
        mapping_replay: _ReplayReceipt,
    ) -> DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelAuditReceipt:
        if not isinstance(chain, _ChainLike):
            raise TypeError("chain must be chain-like with chain_id, chain_hash, and entries")
        if not isinstance(mapping, _MappingReceipt):
            raise TypeError(
                "mapping must be a "
                "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReceipt"
            )
        if not isinstance(
            mapping_replay,
            _ReplayReceipt,
        ):
            raise TypeError(
                "mapping_replay must be a "
                "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt"
            )

        chain_binding = self.chain_binding_verifier.verify(
            chain=chain,
            mapping=mapping,
            mapping_replay=mapping_replay,
        )
        chain_persistence = self.chain_persistence_verifier.verify(
            mapping=mapping,
            mapping_replay=mapping_replay,
        )
        replay_persistence = self.replay_persistence_verifier.verify(mapping_replay)

        mismatches = () if chain_binding.chain_matches else chain_binding.mismatches
        if not chain_persistence.matches:
            mismatches = mismatches + chain_persistence.mismatches
        if not replay_persistence.matches:
            mismatches = mismatches + replay_persistence.mismatches

        mapping_present = self._chain_contains_entry(chain.entries, mapping.mapping_id)
        replay_present = self._chain_contains_entry(chain.entries, mapping_replay.verification_id)
        if not mapping_present:
            mismatches = mismatches + ("mapping_entry_missing_in_chain",)
        if not replay_present:
            mismatches = mismatches + ("mapping_replay_entry_missing_in_chain",)

        mismatches = tuple(dict.fromkeys(m for m in mismatches if m))
        matches = (
            chain_binding.chain_matches
            and chain_persistence.matches
            and replay_persistence.matches
            and mapping_present
            and replay_present
        )
        decision = "READY" if matches else "BLOCKED"
        return (
            DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelAuditReceipt(
                chain_id=chain.chain_id,
                chain_hash=chain.chain_hash,
                chain_entry_count=len(chain.entries),
                mapping_id=mapping.mapping_id,
                mapping_replay_verification_id=mapping_replay.verification_id,
                mapping_chain_binding=chain_binding,
                mapping_chain_persistence=chain_persistence,
                mapping_replay_persistence=replay_persistence,
                chain_entry_mapping_presence=mapping_present,
                chain_entry_mapping_replay_presence=replay_present,
                matches=matches,
                mismatches=mismatches,
                decision=decision,
            )
        )

    @staticmethod
    def _chain_contains_entry(entries: tuple[object, ...], entry_id: str) -> bool:
        for entry in entries:
            current = getattr(entry, "entry_id", None)
            if current == entry_id:
                return True
        return False


__all__ = [
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelAuditReceipt",
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelVerifier",
]
