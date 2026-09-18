from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from smart_money.application.durable_recovery_gated_ingestion import (
    DurableRecoveryGatedIngestionReceipt,
)
from smart_money.application.durable_run_audit_recovery_gate import (
    DurableRunAuditRecoveryGateDecision,
    FailClosedDurableRunAuditRecoveryGate,
)
from smart_money.application.durable_run_receipt_audit import (
    DurableRunReceiptAuditManifest,
)
from smart_money.application.ports.durable_run_receipt_audit_manifest_store import (
    DurableRunReceiptAuditManifestStore,
)
from smart_money.application.trusted_durable_run_audit_head import (
    TrustedDurableRunAuditHead,
    TrustedDurableRunAuditHeadStore,
    advance_trusted_durable_run_audit_head,
)
from smart_money.core.ids import deterministic_id
from smart_money.domain.market_identity import MarketId

_SCHEMA = "fully_audit_gated_ingestion.v1"


@runtime_checkable
class DurableIngestionOperation(Protocol):
    async def run(
        self,
        market: MarketId,
        *,
        max_events: int | None = None,
        advance_if_required: bool = False,
    ) -> DurableRecoveryGatedIngestionReceipt: ...


@runtime_checkable
class DurableRunAuditOperation(Protocol):
    def run(self) -> DurableRunReceiptAuditManifest: ...


@dataclass(frozen=True, slots=True)
class FullyAuditGatedIngestionResult:
    result_id: str
    gate_decision: DurableRunAuditRecoveryGateDecision
    ingestion_receipt: DurableRecoveryGatedIngestionReceipt
    audit_manifest: DurableRunReceiptAuditManifest
    trusted_head: TrustedDurableRunAuditHead
    schema_version: str = _SCHEMA

    def identity_payload(self) -> dict[str, object]:
        return {
            "audit_id": self.audit_manifest.audit_id,
            "gate_decision_id": self.gate_decision.decision_id,
            "ingestion_receipt_id": self.ingestion_receipt.receipt_id,
            "schema_version": self.schema_version,
            "trusted_anchor_id": self.trusted_head.anchor_id,
        }

    def __post_init__(self) -> None:
        if self.audit_manifest.rejected_count:
            raise ValueError("result cannot include a rejected audit manifest")
        if self.result_id != deterministic_id(
            "fully_audit_gated_ingestion",
            self.identity_payload(),
        ):
            raise ValueError("result_id does not match deterministic payload")


@dataclass(frozen=True, slots=True)
class FullyAuditGatedIngestionOrchestrator:
    gate: FailClosedDurableRunAuditRecoveryGate
    ingestion: DurableIngestionOperation
    audit: DurableRunAuditOperation
    audit_store: DurableRunReceiptAuditManifestStore
    head_store: TrustedDurableRunAuditHeadStore

    async def run(
        self,
        market: MarketId,
        *,
        max_events: int | None = None,
        advance_if_required: bool = False,
    ) -> FullyAuditGatedIngestionResult:
        gate_decision = self.gate.open_or_raise(
            advance_if_required=advance_if_required
        )
        receipt = await self.ingestion.run(
            market,
            max_events=max_events,
            advance_if_required=advance_if_required,
        )
        manifest = self.audit.run()
        if manifest.rejected_count:
            raise RuntimeError("post-ingestion durable-run audit rejected a run")
        if self.audit_store.append(manifest) != manifest.audit_id:
            raise RuntimeError("audit store returned a mismatched identity")
        if self.audit_store.get(manifest.audit_id) != manifest:
            raise RuntimeError("audit store did not retain the manifest")
        head = advance_trusted_durable_run_audit_head(
            manifest_store=self.audit_store,
            head_store=self.head_store,
        )
        payload = {
            "audit_id": manifest.audit_id,
            "gate_decision_id": gate_decision.decision_id,
            "ingestion_receipt_id": receipt.receipt_id,
            "schema_version": _SCHEMA,
            "trusted_anchor_id": head.anchor_id,
        }
        return FullyAuditGatedIngestionResult(
            result_id=deterministic_id(
                "fully_audit_gated_ingestion",
                payload,
            ),
            gate_decision=gate_decision,
            ingestion_receipt=receipt,
            audit_manifest=manifest,
            trusted_head=head,
        )


__all__ = [
    "DurableIngestionOperation",
    "DurableRunAuditOperation",
    "FullyAuditGatedIngestionOrchestrator",
    "FullyAuditGatedIngestionResult",
]
