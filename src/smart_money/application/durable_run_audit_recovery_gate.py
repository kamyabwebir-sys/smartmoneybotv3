from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from smart_money.application.ports.durable_run_receipt_audit_manifest_store import (
    DurableRunReceiptAuditManifestStore,
)
from smart_money.application.trusted_durable_run_audit_head import (
    TrustedDurableRunAuditHeadStatus,
    TrustedDurableRunAuditHeadStore,
    advance_trusted_durable_run_audit_head,
    verify_trusted_durable_run_audit_head,
)
from smart_money.core.ids import deterministic_id

_SCHEMA = "durable_run_audit_recovery_gate.v1"


class DurableRunAuditRecoveryGateStatus(str, Enum):
    READY_CURRENT = "READY_CURRENT"
    READY_ADVANCED = "READY_ADVANCED"
    BLOCKED_MISSING_HEAD = "BLOCKED_MISSING_HEAD"
    BLOCKED_ADVANCE_REQUIRED = "BLOCKED_ADVANCE_REQUIRED"
    BLOCKED_ROLLBACK = "BLOCKED_ROLLBACK"
    BLOCKED_DIVERGED = "BLOCKED_DIVERGED"


@dataclass(frozen=True, slots=True)
class DurableRunAuditRecoveryGateDecision:
    decision_id: str
    status: DurableRunAuditRecoveryGateStatus
    allowed: bool
    anchor_id: str | None
    verification_id: str | None
    manifest_store_hash: str
    manifest_count: int
    latest_audit_id: str | None
    schema_version: str = _SCHEMA

    def identity_payload(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "anchor_id": self.anchor_id,
            "latest_audit_id": self.latest_audit_id,
            "manifest_count": self.manifest_count,
            "manifest_store_hash": self.manifest_store_hash,
            "schema_version": self.schema_version,
            "status": self.status.value,
            "verification_id": self.verification_id,
        }

    def __post_init__(self) -> None:
        expected_allowed = self.status in {
            DurableRunAuditRecoveryGateStatus.READY_CURRENT,
            DurableRunAuditRecoveryGateStatus.READY_ADVANCED,
        }
        if self.allowed != expected_allowed:
            raise ValueError("allowed must agree with gate status")
        if self.decision_id != deterministic_id(
            "durable_run_audit_recovery_gate",
            self.identity_payload(),
        ):
            raise ValueError("decision_id does not match deterministic payload")


class DurableRunAuditRecoveryGateBlockedError(RuntimeError):
    def __init__(self, decision: DurableRunAuditRecoveryGateDecision) -> None:
        self.decision = decision
        super().__init__(f"durable-run audit gate blocked: {decision.status}")


@dataclass(frozen=True, slots=True)
class FailClosedDurableRunAuditRecoveryGate:
    manifest_store: DurableRunReceiptAuditManifestStore
    head_store: TrustedDurableRunAuditHeadStore

    def evaluate(
        self,
        *,
        advance_if_required: bool = False,
    ) -> DurableRunAuditRecoveryGateDecision:
        try:
            head = self.head_store.load()
        except FileNotFoundError:
            if not advance_if_required:
                return self._decision(
                    status=(
                        DurableRunAuditRecoveryGateStatus.BLOCKED_MISSING_HEAD
                    ),
                    head=None,
                    verification=None,
                )
            head = advance_trusted_durable_run_audit_head(
                manifest_store=self.manifest_store,
                head_store=self.head_store,
            )
            verification = verify_trusted_durable_run_audit_head(
                head=head,
                manifest_store=self.manifest_store,
            )
            return self._decision(
                status=DurableRunAuditRecoveryGateStatus.READY_ADVANCED,
                head=head,
                verification=verification,
            )
        verification = verify_trusted_durable_run_audit_head(
            head=head,
            manifest_store=self.manifest_store,
        )
        mapping = {
            TrustedDurableRunAuditHeadStatus.CURRENT: (
                DurableRunAuditRecoveryGateStatus.READY_CURRENT
            ),
            TrustedDurableRunAuditHeadStatus.ADVANCE_REQUIRED: (
                DurableRunAuditRecoveryGateStatus.BLOCKED_ADVANCE_REQUIRED
            ),
            TrustedDurableRunAuditHeadStatus.ROLLBACK: (
                DurableRunAuditRecoveryGateStatus.BLOCKED_ROLLBACK
            ),
            TrustedDurableRunAuditHeadStatus.DIVERGED: (
                DurableRunAuditRecoveryGateStatus.BLOCKED_DIVERGED
            ),
        }
        if (
            verification.status
            is TrustedDurableRunAuditHeadStatus.ADVANCE_REQUIRED
            and advance_if_required
        ):
            head = advance_trusted_durable_run_audit_head(
                manifest_store=self.manifest_store,
                head_store=self.head_store,
            )
            verification = verify_trusted_durable_run_audit_head(
                head=head,
                manifest_store=self.manifest_store,
            )
            status = DurableRunAuditRecoveryGateStatus.READY_ADVANCED
        else:
            status = mapping[verification.status]
        return self._decision(
            status=status,
            head=head,
            verification=verification,
        )

    def open_or_raise(
        self,
        *,
        advance_if_required: bool = False,
    ) -> DurableRunAuditRecoveryGateDecision:
        decision = self.evaluate(advance_if_required=advance_if_required)
        if not decision.allowed:
            raise DurableRunAuditRecoveryGateBlockedError(decision)
        return decision

    def _decision(self, *, status, head, verification):
        manifests = tuple(self.manifest_store.iter_manifests())
        latest_without_verification = (
            None if not manifests else manifests[-1].audit_id
        )
        payload = {
            "allowed": status
            in {
                DurableRunAuditRecoveryGateStatus.READY_CURRENT,
                DurableRunAuditRecoveryGateStatus.READY_ADVANCED,
            },
            "anchor_id": None if head is None else head.anchor_id,
            "latest_audit_id": (
                latest_without_verification
                if verification is None
                else verification.current_latest_audit_id
            ),
            "manifest_count": (
                self.manifest_store.manifest_count
                if verification is None
                else verification.current_manifest_count
            ),
            "manifest_store_hash": (
                self.manifest_store.content_hash
                if verification is None
                else verification.current_store_hash
            ),
            "schema_version": _SCHEMA,
            "status": status.value,
            "verification_id": (
                None if verification is None else verification.verification_id
            ),
        }
        return DurableRunAuditRecoveryGateDecision(
            decision_id=deterministic_id(
                "durable_run_audit_recovery_gate",
                payload,
            ),
            status=status,
            allowed=payload["allowed"],
            anchor_id=payload["anchor_id"],
            verification_id=payload["verification_id"],
            manifest_store_hash=payload["manifest_store_hash"],
            manifest_count=payload["manifest_count"],
            latest_audit_id=payload["latest_audit_id"],
        )


__all__ = [
    "DurableRunAuditRecoveryGateBlockedError",
    "DurableRunAuditRecoveryGateDecision",
    "DurableRunAuditRecoveryGateStatus",
    "FailClosedDurableRunAuditRecoveryGate",
]
