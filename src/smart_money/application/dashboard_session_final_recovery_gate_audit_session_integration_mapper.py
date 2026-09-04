from __future__ import annotations

from dataclasses import dataclass

from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_full_audit_binding as binding_model,
)
from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_recovery_full_audit_verifier as full_audit_model,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_chain import (
    DashboardSessionFinalRecoveryGateAuditChain,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt:
    chain_id: str
    chain_hash: str
    chain_entry_count: int
    chain_replay_verification_id: str | None
    full_audit_receipt_id: str
    full_audit_verification_id: str
    binding_receipt_id: str
    integration_session_id: str
    previous_integration_session_id: str | None
    decision: str
    reason_code: str
    schema_version: str = (
        "dashboard_session_final_recovery_gate_audit_session_integration.v1"
    )

    def __post_init__(self) -> None:
        for name in (
            "chain_id",
            "chain_hash",
            "full_audit_receipt_id",
            "full_audit_verification_id",
            "binding_receipt_id",
            "reason_code",
            "integration_session_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.chain_entry_count < 0:
            raise ValueError("chain_entry_count must be non-negative")
        if not isinstance(self.chain_entry_count, int) or isinstance(
            self.chain_entry_count, bool
        ):
            raise ValueError("chain_entry_count must be a non-negative integer")
        for name in ("previous_integration_session_id",):
            value = getattr(self, name)
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                raise ValueError(
                    f"{name} must be a non-empty string or None"
                )
        if (
            self.chain_replay_verification_id is not None
            and not isinstance(self.chain_replay_verification_id, str)
        ):
            raise TypeError("chain_replay_verification_id must be a string or None")
        if not self.chain_hash:
            raise ValueError("chain_hash must not be empty")
        if len(self.chain_hash) != 64:
            raise ValueError("chain_hash must be a SHA-256 hex digest")
        if self.decision not in {"READY", "BLOCKED"}:
            raise ValueError("decision must be READY or BLOCKED")
        if (
            self.schema_version
            != "dashboard_session_final_recovery_gate_audit_session_integration.v1"
        ):
            raise ValueError(
                "unsupported session integration mapping schema_version"
            )

    @property
    def mapping_id(self) -> str:
        return deterministic_id(
            "dashboard_session_final_recovery_gate_audit_session_integration",
            self.canonical_dict(),
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "binding_receipt_id": self.binding_receipt_id,
            "chain_entry_count": self.chain_entry_count,
            "chain_hash": self.chain_hash,
            "chain_id": self.chain_id,
            "chain_replay_verification_id": self.chain_replay_verification_id,
            "decision": self.decision,
            "full_audit_receipt_id": self.full_audit_receipt_id,
            "full_audit_verification_id": self.full_audit_verification_id,
            "integration_session_id": self.integration_session_id,
            "previous_integration_session_id": self.previous_integration_session_id,
            "reason_code": self.reason_code,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditSessionIntegrationMapper:
    def map(
        self,
        chain: DashboardSessionFinalRecoveryGateAuditChain,
        full_audit_receipt: (
            full_audit_model.DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditReceipt
        ),
        binding_receipt: (
            binding_model.DashboardSessionFinalRecoveryGateAuditFullAuditBindingReceipt
        ),
        previous_mapping: (
            DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt | None
        ) = None,
        chain_replay_verification_id: str | None = None,
    ) -> DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt:
        if not isinstance(chain, DashboardSessionFinalRecoveryGateAuditChain):
            raise TypeError(
                "chain must be a "
                "DashboardSessionFinalRecoveryGateAuditChain"
            )
        if not isinstance(
            full_audit_receipt,
            full_audit_model.DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditReceipt,
        ):
            raise TypeError(
                "full_audit_receipt must be a "
                "DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditReceipt"
            )
        if not isinstance(
            binding_receipt,
            binding_model.DashboardSessionFinalRecoveryGateAuditFullAuditBindingReceipt,
        ):
            raise TypeError(
                "binding_receipt must be a "
                "DashboardSessionFinalRecoveryGateAuditFullAuditBindingReceipt"
            )
        if previous_mapping is not None and not isinstance(
            previous_mapping,
            DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
        ):
            raise TypeError(
                "previous_mapping must be a "
                "DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt"
            )

        if chain.chain_id != full_audit_receipt.expected_chain_id:
            return _blocked(
                chain,
                full_audit_receipt,
                binding_receipt,
                previous_mapping,
                chain_replay_verification_id,
                "CHAIN_MISMATCH",
            )
        if chain.chain_hash != full_audit_receipt.expected_chain_hash:
            return _blocked(
                chain,
                full_audit_receipt,
                binding_receipt,
                previous_mapping,
                chain_replay_verification_id,
                "CHAIN_HASH_MISMATCH",
            )
        if chain.chain_id != binding_receipt.chain_id or (
            chain.chain_hash != binding_receipt.chain_hash
        ):
            return _blocked(
                chain,
                full_audit_receipt,
                binding_receipt,
                previous_mapping,
                chain_replay_verification_id,
                "BINDING_CHAIN_MISMATCH",
            )
        if not full_audit_receipt.matches:
            return _blocked(
                chain,
                full_audit_receipt,
                binding_receipt,
                previous_mapping,
                chain_replay_verification_id,
                "FULL_AUDIT_MISMATCH",
            )
        if binding_receipt.decision != "READY":
            return _blocked(
                chain,
                full_audit_receipt,
                binding_receipt,
                previous_mapping,
                chain_replay_verification_id,
                "BINDING_BLOCKED",
            )
        if (
            binding_receipt.full_audit_id != full_audit_receipt.full_audit_id
            or binding_receipt.full_audit_verification_id
            != full_audit_receipt.recovery_replay_verification_id
        ):
            return _blocked(
                chain,
                full_audit_receipt,
                binding_receipt,
                previous_mapping,
                chain_replay_verification_id,
                "BINDING_FULL_AUDIT_LINK_MISMATCH",
            )

        if previous_mapping is not None:
            if (
                previous_mapping.chain_id != chain.chain_id
                or previous_mapping.chain_hash != chain.chain_hash
            ):
                return _blocked(
                    chain,
                    full_audit_receipt,
                    binding_receipt,
                    previous_mapping,
                    chain_replay_verification_id,
                    "PREVIOUS_MAPPING_CHAIN_MISMATCH",
                )

        return DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt(
            chain_id=chain.chain_id,
            chain_hash=chain.chain_hash,
            chain_entry_count=len(chain.entries),
            chain_replay_verification_id=(
                chain_replay_verification_id
                if chain_replay_verification_id is not None
                else binding_receipt.head_anchor_id
            ),
            full_audit_receipt_id=full_audit_receipt.full_audit_id,
            full_audit_verification_id=full_audit_receipt.recovery_replay_verification_id,
            binding_receipt_id=binding_receipt.receipt_id,
            integration_session_id="integration-session",
            previous_integration_session_id=(
                None if previous_mapping is None else previous_mapping.mapping_id
            ),
            decision="READY",
            reason_code="CHAIN_RECEIPT_INTEGRATION_READY",
        )


def _blocked(
    chain: DashboardSessionFinalRecoveryGateAuditChain,
    full_audit_receipt: (
        full_audit_model.DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditReceipt
    ),
    binding_receipt: binding_model.DashboardSessionFinalRecoveryGateAuditFullAuditBindingReceipt,
    previous_mapping: (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt | None
    ),
    chain_replay_verification_id: str | None,
    reason_code: str,
) -> DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt:
    return DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt(
        chain_id=chain.chain_id,
        chain_hash=chain.chain_hash,
        chain_entry_count=len(chain.entries),
        chain_replay_verification_id=chain_replay_verification_id,
        full_audit_receipt_id=full_audit_receipt.full_audit_id,
        full_audit_verification_id=full_audit_receipt.recovery_replay_verification_id,
        binding_receipt_id=binding_receipt.receipt_id,
        integration_session_id="integration-session",
        previous_integration_session_id=(
            None if previous_mapping is None else previous_mapping.mapping_id
        ),
        decision="BLOCKED",
        reason_code=reason_code,
    )


__all__ = [
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt",
    "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMapper",
]
