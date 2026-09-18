from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapper import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_verifier import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = (
    "dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain.v1"
)


@runtime_checkable
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReceiptStore(Protocol):
    def get(
        self, mapping_id: str
    ) -> DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt | None: ...


@runtime_checkable
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceiptStore(
    Protocol
):
    def get(
        self, verification_id: str
    ) -> DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt | None: ...


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceAuditReceipt:
    expected_mapping_id: str
    persisted_mapping_id: str | None
    mapping_matches: bool
    expected_replay_verification_id: str
    persisted_replay_verification_id: str | None
    replay_matches: bool
    mismatch_mapping_replay_link: bool
    mismatches: tuple[str, ...] = ()
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "expected_mapping_id",
            "expected_replay_verification_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")

        if self.persisted_mapping_id is not None and (
            not isinstance(self.persisted_mapping_id, str) or not self.persisted_mapping_id.strip()
        ):
            raise ValueError("persisted_mapping_id must be a non-empty string or None")
        if self.persisted_replay_verification_id is not None and (
            not isinstance(self.persisted_replay_verification_id, str)
            or not self.persisted_replay_verification_id.strip()
        ):
            raise ValueError(
                "persisted_replay_verification_id must be a non-empty string or None"
            )
        if not isinstance(self.mapping_matches, bool):
            raise TypeError("mapping_matches must be a boolean")
        if not isinstance(self.replay_matches, bool):
            raise TypeError("replay_matches must be a boolean")
        if not isinstance(self.mismatch_mapping_replay_link, bool):
            raise TypeError("mismatch_mapping_replay_link must be a boolean")
        if not isinstance(self.mismatches, tuple) or not all(
            isinstance(item, str) and item.strip() for item in self.mismatches
        ):
            raise TypeError("mismatches must be a tuple of text values")
        if not self.mapping_matches and (not self.mismatches):
            raise ValueError("non-matching mapping requires mismatches")
        if self.mapping_matches and self.replay_matches and self.mismatch_mapping_replay_link:
            raise ValueError("link mismatch is not possible when both artifacts match")
        if self.mapping_matches and not self.mismatches and not self.replay_matches:
            raise ValueError("non-matching replay requires mismatch reason")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported session integration mapping chain persistence schema_version")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "expected_mapping_id": self.expected_mapping_id,
            "expected_replay_verification_id": self.expected_replay_verification_id,
            "mapping_matches": self.mapping_matches,
            "persisted_mapping_id": self.persisted_mapping_id,
            "replay_matches": self.replay_matches,
            "persisted_replay_verification_id": self.persisted_replay_verification_id,
            "mismatch_mapping_replay_link": self.mismatch_mapping_replay_link,
            "mismatches": list(self.mismatches),
            "schema_version": self.schema_version,
        }

    @property
    def matches(self) -> bool:
        return (
            self.mapping_matches
            and self.replay_matches
            and not self.mismatch_mapping_replay_link
        )

    @property
    def audit_id(self) -> str:
        return deterministic_id(
            "dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_persistence_audit",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceVerifier:
    mapping_store: DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReceiptStore
    replay_store: DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceiptStore

    def verify(
        self,
        mapping: DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
        mapping_replay: DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt,
    ) -> DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceAuditReceipt:
        if not isinstance(
            mapping,
            DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
        ):
            raise TypeError("mapping must be a DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt")
        if not isinstance(
            mapping_replay,
            DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt,
        ):
            raise TypeError(
                "mapping_replay must be a DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt"
            )

        persisted_mapping = self.mapping_store.get(mapping.mapping_id)
        if persisted_mapping is None or persisted_mapping != mapping:
            mapping_matches = False
            mapping_mismatches = ("persisted_session_integration_mapping_missing",)
            if persisted_mapping is not None:
                mapping_mismatches = ("persisted_session_integration_mapping_mismatch",)
            mismatches = mapping_mismatches
            persisted_mapping_id = (
                persisted_mapping.mapping_id if persisted_mapping is not None else None
            )
        else:
            mapping_matches = True
            mismatches: tuple[str, ...] = ()
            persisted_mapping_id = persisted_mapping.mapping_id

        if mapping_replay.expected_mapping_id != mapping.mapping_id:
            replay_link_mismatch = True
        else:
            replay_link_mismatch = False

        persisted_replay = self.replay_store.get(mapping_replay.verification_id)
        if persisted_replay is None or persisted_replay != mapping_replay:
            replay_matches = False
            replay_mismatches = ("persisted_session_integration_mapping_replay_missing",)
            if persisted_replay is not None:
                replay_mismatches = ("persisted_session_integration_mapping_replay_mismatch",)
            mismatches = mismatches + replay_mismatches
            persisted_replay_verification_id = (
                persisted_replay.verification_id if persisted_replay is not None else None
            )
        else:
            replay_matches = True
            persisted_replay_verification_id = mapping_replay.verification_id
            if replay_link_mismatch:
                mismatches = mismatches + ("mapping_replay_link_mismatch",)

        if replay_link_mismatch:
            mismatches = mismatches + ("mapping_replay_link_mismatch",)

        if persisted_replay is not None and replay_link_mismatch:
            mismatches = tuple(dict.fromkeys(mismatches))
            # remove replay missing/mismatch if present from a mismatched mapping replay object
            mismatches = tuple(item for item in mismatches if item not in {"persisted_session_integration_mapping_replay_missing", "persisted_session_integration_mapping_replay_mismatch"})

        return DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceAuditReceipt(
            expected_mapping_id=mapping.mapping_id,
            persisted_mapping_id=persisted_mapping_id,
            mapping_matches=mapping_matches,
            expected_replay_verification_id=mapping_replay.verification_id,
            persisted_replay_verification_id=persisted_replay_verification_id,
            replay_matches=replay_matches,
            mismatch_mapping_replay_link=replay_link_mismatch,
            mismatches=mismatches,
        )


__all__ = [
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceAuditReceipt",
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceVerifier",
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReceiptStore",
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceiptStore",
]
