from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapper import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_verifier import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceAuditReceipt,
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_persistence_verifier import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceAuditReceipt,
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_verifier import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = (
    "dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_binding.v1"
)


@runtime_checkable
class _ChainLike(Protocol):
    chain_id: str
    chain_hash: str
    entries: tuple[object, ...]


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainBindingReceipt:
    chain_id: str
    chain_hash: str
    chain_entry_count: int
    expected_mapping_id: str
    expected_mapping_replay_verification_id: str
    persisted_chain_persistence_verification: bool
    persisted_mapping_replay_persistence_verification: bool
    chain_matches: bool
    mismatches: tuple[str, ...] = ()
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.chain_id, str) or not self.chain_id.strip():
            raise ValueError("chain_id must be a non-empty string")
        if not isinstance(self.chain_hash, str) or not self.chain_hash.strip():
            raise ValueError("chain_hash must be a non-empty string")
        if not isinstance(self.chain_entry_count, int) or isinstance(
            self.chain_entry_count, bool
        ):
            raise ValueError("chain_entry_count must be a non-negative integer")
        if self.chain_entry_count < 0:
            raise ValueError("chain_entry_count must be a non-negative integer")
        if not isinstance(self.expected_mapping_id, str) or not self.expected_mapping_id.strip():
            raise ValueError("expected_mapping_id must be a non-empty string")
        if not isinstance(
            self.expected_mapping_replay_verification_id, str
        ) or not self.expected_mapping_replay_verification_id.strip():
            raise ValueError(
                "expected_mapping_replay_verification_id must be a non-empty string"
            )
        if not isinstance(self.persisted_chain_persistence_verification, bool):
            raise TypeError(
                "persisted_chain_persistence_verification must be a boolean"
            )
        if not isinstance(
            self.persisted_mapping_replay_persistence_verification, bool
        ):
            raise TypeError(
                "persisted_mapping_replay_persistence_verification must be a boolean"
            )
        if not isinstance(self.chain_matches, bool):
            raise TypeError("chain_matches must be a boolean")
        if not isinstance(self.mismatches, tuple) or not all(
            isinstance(item, str) and item.strip() for item in self.mismatches
        ):
            raise TypeError("mismatches must be a tuple of text values")
        if self.chain_matches and self.mismatches:
            raise ValueError("matching chain binding cannot contain mismatches")
        if not self.chain_matches and not self.mismatches:
            raise ValueError("non-matching chain binding requires mismatches")
        if (
            self.persisted_chain_persistence_verification
            and self.persisted_mapping_replay_persistence_verification is False
            and "mapping_replay_persistence" in self.mismatches
        ):
            pass
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError(
                "unsupported session integration mapping chain binding schema_version"
            )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "chain_entry_count": self.chain_entry_count,
            "chain_hash": self.chain_hash,
            "chain_id": self.chain_id,
            "chain_matches": self.chain_matches,
            "expected_mapping_id": self.expected_mapping_id,
            "expected_mapping_replay_verification_id": self.expected_mapping_replay_verification_id,
            "mismatches": list(self.mismatches),
            "persisted_chain_persistence_verification": self.persisted_chain_persistence_verification,
            "persisted_mapping_replay_persistence_verification": self.persisted_mapping_replay_persistence_verification,
            "schema_version": self.schema_version,
        }

    @property
    def integration_binding_id(self) -> str:
        return deterministic_id(
            "dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_binding",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainBindingVerifier:
    chain_persistence_verifier: (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceVerifier
    ) = field(
        default_factory=DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceVerifier,
    )
    replay_persistence_verifier: (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceVerifier
    ) = field(
        default_factory=DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceVerifier,
    )

    def verify(
        self,
        chain: _ChainLike,
        mapping: DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
        mapping_replay: DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt,
    ) -> DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainBindingReceipt:
        if not isinstance(mapping, DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt):
            raise TypeError(
                "mapping must be a "
                "DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt"
            )
        if not isinstance(
            mapping_replay,
            DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt,
        ):
            raise TypeError(
                "mapping_replay must be a "
                "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt"
            )
        if not hasattr(chain, "chain_id") or not hasattr(chain, "entries"):
            raise TypeError("chain must be chain-like with chain_id and entries")
        if not isinstance(chain.entries, tuple):
            raise TypeError("chain.entries must be a tuple")

        persistence_receipt: DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceAuditReceipt = (
            self.chain_persistence_verifier.verify(mapping=mapping, mapping_replay=mapping_replay)
        )
        replay_persistence_receipt: DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceAuditReceipt = (
            self.replay_persistence_verifier.verify(mapping_replay)
        )

        links_match = (
            mapping.chain_id == chain.chain_id
            and mapping.chain_hash == chain.chain_hash
            and mapping.chain_entry_count == len(chain.entries)
            and mapping_replay.expected_mapping_id == mapping.mapping_id
            and mapping_replay.matches
        )
        mismatches = ()
        if not persistence_receipt.matches:
            mismatches = mismatches + persistence_receipt.mismatches
        if not replay_persistence_receipt.matches:
            mismatches = mismatches + replay_persistence_receipt.mismatches
        if not links_match:
            mismatches = mismatches + ("integration_mapping_chain_link_mismatch",)
            if mapping.chain_id != chain.chain_id:
                mismatches = mismatches + ("chain_id_mismatch",)
            if mapping.chain_hash != chain.chain_hash:
                mismatches = mismatches + ("chain_hash_mismatch",)
            if mapping.chain_entry_count != len(chain.entries):
                mismatches = mismatches + ("chain_entry_count_mismatch",)
            if mapping_replay.expected_mapping_id != mapping.mapping_id:
                mismatches = mismatches + ("replay_expected_mapping_id_mismatch",)

        if not mapping_replay.matches:
            mismatches = mismatches + ("mapping_replay_is_not_matching",)

        mismatches = tuple(dict.fromkeys(mismatches))
        chain_matches = (
            links_match
            and persistence_receipt.matches
            and replay_persistence_receipt.matches
        )
        return DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainBindingReceipt(
            chain_id=chain.chain_id,
            chain_hash=chain.chain_hash,
            chain_entry_count=len(chain.entries),
            expected_mapping_id=mapping.mapping_id,
            expected_mapping_replay_verification_id=mapping_replay.verification_id,
            persisted_chain_persistence_verification=persistence_receipt.matches,
            persisted_mapping_replay_persistence_verification=replay_persistence_receipt.matches,
            chain_matches=chain_matches,
            mismatches=mismatches,
        )


__all__ = [
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainBindingVerifier",
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainBindingReceipt",
]
