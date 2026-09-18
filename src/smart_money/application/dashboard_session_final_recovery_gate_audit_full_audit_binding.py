from __future__ import annotations

from dataclasses import dataclass

from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_recovery_full_audit_verifier as full_audit_model,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_chain import (
    DashboardSessionFinalRecoveryGateAuditChain,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditFullAuditHeadAnchor:
    chain_id: str
    chain_hash: str
    entry_count: int
    latest_full_audit_id: str
    latest_full_audit_verification_id: str
    reason_code: str
    previous_anchor_id: str | None
    schema_version: str = (
        "dashboard_session_final_recovery_gate_audit_full_audit_head_anchor.v1"
    )

    def __post_init__(self) -> None:
        for name in (
            "chain_id",
            "chain_hash",
            "latest_full_audit_id",
            "reason_code",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if (
            not isinstance(self.latest_full_audit_verification_id, str)
            or not self.latest_full_audit_verification_id.strip()
        ):
            raise ValueError(
                "latest_full_audit_verification_id must be a non-empty string"
            )
        if len(self.chain_hash) != 64:
            raise ValueError("chain_hash must be a SHA-256 hex digest")
        if (
            not isinstance(self.entry_count, int)
            or isinstance(self.entry_count, bool)
            or self.entry_count < 0
        ):
            raise ValueError("entry_count must be a non-negative integer")
        if self.previous_anchor_id is not None and (
            not isinstance(self.previous_anchor_id, str)
            or not self.previous_anchor_id.strip()
        ):
            raise ValueError("previous_anchor_id must be a non-empty string or None")
        if (
            self.schema_version
            != "dashboard_session_final_recovery_gate_audit_full_audit_head_anchor.v1"
        ):
            raise ValueError("unsupported full audit head anchor schema_version")

    @classmethod
    def from_chain(
        cls,
        chain: DashboardSessionFinalRecoveryGateAuditChain,
        full_audit: full_audit_model.DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditReceipt,
        previous_anchor_id: str | None,
    ) -> "DashboardSessionFinalRecoveryGateAuditFullAuditHeadAnchor":
        if not isinstance(chain, DashboardSessionFinalRecoveryGateAuditChain):
            raise TypeError("chain must be a DashboardSessionFinalRecoveryGateAuditChain")
        if not isinstance(
            full_audit,
            full_audit_model.DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditReceipt,
        ):
            raise TypeError(
                "full_audit must be a "
                "DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditReceipt"
            )
        if previous_anchor_id is not None and (
            not isinstance(previous_anchor_id, str) or not previous_anchor_id.strip()
        ):
            raise ValueError("previous_anchor_id must be a non-empty string or None")
        return cls(
            chain_id=chain.chain_id,
            chain_hash=chain.chain_hash,
            entry_count=len(chain.entries),
            latest_full_audit_id=full_audit.full_audit_id,
            latest_full_audit_verification_id=full_audit.recovery_replay_verification_id,
            reason_code="FULL_AUDIT_BOUND",
            previous_anchor_id=previous_anchor_id,
        )

    def matches(
        self,
        chain: DashboardSessionFinalRecoveryGateAuditChain,
        full_audit: full_audit_model.DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditReceipt,
        previous_anchor_id: str | None,
    ) -> bool:
        try:
            return self == self.__class__.from_chain(chain, full_audit, previous_anchor_id)
        except (TypeError, ValueError):
            return False

    def canonical_dict(self) -> dict[str, object]:
        return {
            "chain_hash": self.chain_hash,
            "chain_id": self.chain_id,
            "entry_count": self.entry_count,
            "latest_full_audit_id": self.latest_full_audit_id,
            "latest_full_audit_verification_id": self.latest_full_audit_verification_id,
            "previous_anchor_id": self.previous_anchor_id,
            "reason_code": self.reason_code,
            "schema_version": self.schema_version,
        }

    @property
    def anchor_id(self) -> str:
        return deterministic_id(
            "dashboard_session_final_recovery_gate_audit_full_audit_head_anchor",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditFullAuditBindingReceipt:
    chain_id: str
    chain_hash: str
    full_audit_id: str
    full_audit_verification_id: str
    head_anchor_id: str
    previous_anchor_id: str | None
    decision: str
    reason_code: str
    schema_version: str = (
        "dashboard_session_final_recovery_gate_audit_full_audit_binding.v1"
    )

    def __post_init__(self) -> None:
        for name in (
            "chain_id",
            "chain_hash",
            "full_audit_id",
            "full_audit_verification_id",
            "head_anchor_id",
            "reason_code",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.previous_anchor_id, str) and self.previous_anchor_id is not None:
            raise TypeError("previous_anchor_id must be a string or None")
        if len(self.chain_hash) != 64:
            raise ValueError("chain_hash must be a SHA-256 hex digest")
        if self.decision not in {"READY", "BLOCKED"}:
            raise ValueError("decision must be READY or BLOCKED")
        if (
            self.schema_version
            != "dashboard_session_final_recovery_gate_audit_full_audit_binding.v1"
        ):
            raise ValueError("unsupported full audit binding schema_version")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "chain_hash": self.chain_hash,
            "chain_id": self.chain_id,
            "decision": self.decision,
            "full_audit_id": self.full_audit_id,
            "full_audit_verification_id": self.full_audit_verification_id,
            "head_anchor_id": self.head_anchor_id,
            "previous_anchor_id": self.previous_anchor_id,
            "reason_code": self.reason_code,
            "schema_version": self.schema_version,
        }

    @property
    def receipt_id(self) -> str:
        return deterministic_id(
            "dashboard_session_final_recovery_gate_audit_full_audit_binding",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditFullAuditBinder:
    def bind(
        self,
        chain: DashboardSessionFinalRecoveryGateAuditChain,
        full_audit: full_audit_model.DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditReceipt,
        previous_anchor: (
            DashboardSessionFinalRecoveryGateAuditFullAuditHeadAnchor | None
        ) = None,
    ) -> DashboardSessionFinalRecoveryGateAuditFullAuditBindingReceipt:
        if not isinstance(chain, DashboardSessionFinalRecoveryGateAuditChain):
            raise TypeError(
                "chain must be a DashboardSessionFinalRecoveryGateAuditChain"
            )
        if not isinstance(
            full_audit,
            full_audit_model.DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditReceipt,
        ):
            raise TypeError(
                "full_audit must be a "
                "DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditReceipt"
            )
        if previous_anchor is not None and not isinstance(
            previous_anchor,
            DashboardSessionFinalRecoveryGateAuditFullAuditHeadAnchor,
        ):
            raise TypeError(
                "previous_anchor must be a "
                "DashboardSessionFinalRecoveryGateAuditFullAuditHeadAnchor"
            )

        if full_audit.expected_chain_id != chain.chain_id:
            return _blocked(
                chain,
                full_audit,
                previous_anchor,
                "FULL_AUDIT_CHAIN_ID_MISMATCH",
            )

        if full_audit.expected_chain_hash != chain.chain_hash:
            return _blocked(
                chain,
                full_audit,
                previous_anchor,
                "FULL_AUDIT_CHAIN_HASH_MISMATCH",
            )

        if previous_anchor is not None and previous_anchor.chain_id != chain.chain_id:
            return _blocked(
                chain,
                full_audit,
                previous_anchor,
                "FULL_AUDIT_PREVIOUS_CHAIN_MISMATCH",
            )
        if previous_anchor is not None and previous_anchor.chain_hash != chain.chain_hash:
            return _blocked(
                chain,
                full_audit,
                previous_anchor,
                "FULL_AUDIT_PREVIOUS_CHAIN_HASH_MISMATCH",
            )

        if not full_audit.matches:
            return _blocked(
                chain,
                full_audit,
                previous_anchor,
                "FULL_AUDIT_MATCH_FAILURE",
            )

        anchor = DashboardSessionFinalRecoveryGateAuditFullAuditHeadAnchor.from_chain(
            chain,
            full_audit,
            previous_anchor.anchor_id if previous_anchor is not None else None,
        )
        return DashboardSessionFinalRecoveryGateAuditFullAuditBindingReceipt(
            chain_id=chain.chain_id,
            chain_hash=chain.chain_hash,
            full_audit_id=full_audit.full_audit_id,
            full_audit_verification_id=full_audit.recovery_replay_verification_id,
            head_anchor_id=anchor.anchor_id,
            previous_anchor_id=previous_anchor.anchor_id
            if previous_anchor is not None
            else None,
            decision="READY",
            reason_code="FULL_AUDIT_CHAIN_BOUND",
        )


def _blocked(
    chain: DashboardSessionFinalRecoveryGateAuditChain,
    full_audit: full_audit_model.DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditReceipt,
    previous_anchor: DashboardSessionFinalRecoveryGateAuditFullAuditHeadAnchor | None,
    reason_code: str,
) -> DashboardSessionFinalRecoveryGateAuditFullAuditBindingReceipt:
    return DashboardSessionFinalRecoveryGateAuditFullAuditBindingReceipt(
        chain_id=chain.chain_id,
        chain_hash=chain.chain_hash,
        full_audit_id=full_audit.full_audit_id,
        full_audit_verification_id=full_audit.recovery_replay_verification_id,
        head_anchor_id="missing-anchor",
        previous_anchor_id=(
            None if previous_anchor is None else previous_anchor.anchor_id
        ),
        decision="BLOCKED",
        reason_code=reason_code,
    )


__all__ = [
    "DashboardSessionFinalRecoveryGateAuditFullAuditHeadAnchor",
    "DashboardSessionFinalRecoveryGateAuditFullAuditBindingReceipt",
    "DashboardSessionFinalRecoveryGateAuditFullAuditBinder",
]
