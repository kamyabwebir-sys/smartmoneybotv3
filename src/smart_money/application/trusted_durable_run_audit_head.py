from __future__ import annotations

import hmac
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from smart_money.application.ports.durable_run_receipt_audit_manifest_store import (
    DurableRunReceiptAuditManifestStore,
)
from smart_money.core.ids import deterministic_id

_HEAD_SCHEMA = "trusted_durable_run_audit_head.v1"
_VERIFICATION_SCHEMA = "trusted_durable_run_audit_head_verification.v1"


class TrustedDurableRunAuditHeadStatus(str, Enum):
    CURRENT = "CURRENT"
    ADVANCE_REQUIRED = "ADVANCE_REQUIRED"
    ROLLBACK = "ROLLBACK"
    DIVERGED = "DIVERGED"


@dataclass(frozen=True, slots=True)
class TrustedDurableRunAuditHead:
    anchor_id: str
    manifest_store_hash: str
    manifest_count: int
    latest_audit_id: str | None
    previous_anchor_id: str | None
    schema_version: str = _HEAD_SCHEMA

    def identity_payload(self) -> dict[str, object]:
        return {
            "latest_audit_id": self.latest_audit_id,
            "manifest_count": self.manifest_count,
            "manifest_store_hash": self.manifest_store_hash,
            "previous_anchor_id": self.previous_anchor_id,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, object]:
        return {"anchor_id": self.anchor_id, **self.identity_payload()}

    def __post_init__(self) -> None:
        if self.manifest_count < 0:
            raise ValueError("manifest_count must be non-negative")
        if (self.manifest_count == 0) != (self.latest_audit_id is None):
            raise ValueError("latest audit presence must agree with count")
        if self.schema_version != _HEAD_SCHEMA:
            raise ValueError("unsupported trusted durable-run head schema")
        if self.anchor_id != deterministic_id(
            "trusted_durable_run_audit_head",
            self.identity_payload(),
        ):
            raise ValueError("anchor_id does not match deterministic payload")


@runtime_checkable
class TrustedDurableRunAuditHeadStore(Protocol):
    def save(self, head: TrustedDurableRunAuditHead) -> str: ...

    def load(self) -> TrustedDurableRunAuditHead: ...


@dataclass(frozen=True, slots=True)
class TrustedDurableRunAuditHeadVerification:
    verification_id: str
    anchor_id: str
    status: TrustedDurableRunAuditHeadStatus
    current_store_hash: str
    current_manifest_count: int
    current_latest_audit_id: str | None
    schema_version: str = _VERIFICATION_SCHEMA

    def identity_payload(self) -> dict[str, object]:
        return {
            "anchor_id": self.anchor_id,
            "current_latest_audit_id": self.current_latest_audit_id,
            "current_manifest_count": self.current_manifest_count,
            "current_store_hash": self.current_store_hash,
            "schema_version": self.schema_version,
            "status": self.status.value,
        }

    def __post_init__(self) -> None:
        if self.verification_id != deterministic_id(
            "trusted_durable_run_audit_head_verification",
            self.identity_payload(),
        ):
            raise ValueError("verification_id does not match payload")


def _snapshot(
    store: DurableRunReceiptAuditManifestStore,
) -> tuple[str, int, str | None]:
    manifests = tuple(store.iter_manifests())
    count = store.manifest_count
    digest = store.content_hash
    if len(manifests) != count:
        raise RuntimeError("manifest store changed during snapshot")
    if any(manifest.rejected_count for manifest in manifests):
        raise ValueError("trusted head cannot anchor a rejected manifest")
    if store.manifest_count != count or not hmac.compare_digest(
        store.content_hash,
        digest,
    ):
        raise RuntimeError("manifest store changed during snapshot")
    return digest, count, None if not manifests else manifests[-1].audit_id


def verify_trusted_durable_run_audit_head(
    *,
    head: TrustedDurableRunAuditHead,
    manifest_store: DurableRunReceiptAuditManifestStore,
) -> TrustedDurableRunAuditHeadVerification:
    digest, count, latest = _snapshot(manifest_store)
    prefix = manifest_store.contains_content_hash(
        head.manifest_store_hash,
        head.manifest_count,
    )
    if count < head.manifest_count:
        status = TrustedDurableRunAuditHeadStatus.ROLLBACK
    elif not prefix:
        status = TrustedDurableRunAuditHeadStatus.DIVERGED
    elif count > head.manifest_count:
        status = TrustedDurableRunAuditHeadStatus.ADVANCE_REQUIRED
    elif digest == head.manifest_store_hash and latest == head.latest_audit_id:
        status = TrustedDurableRunAuditHeadStatus.CURRENT
    else:
        status = TrustedDurableRunAuditHeadStatus.DIVERGED
    payload = {
        "anchor_id": head.anchor_id,
        "current_latest_audit_id": latest,
        "current_manifest_count": count,
        "current_store_hash": digest,
        "schema_version": _VERIFICATION_SCHEMA,
        "status": status.value,
    }
    return TrustedDurableRunAuditHeadVerification(
        verification_id=deterministic_id(
            "trusted_durable_run_audit_head_verification",
            payload,
        ),
        anchor_id=head.anchor_id,
        status=status,
        current_store_hash=digest,
        current_manifest_count=count,
        current_latest_audit_id=latest,
    )


def advance_trusted_durable_run_audit_head(
    *,
    manifest_store: DurableRunReceiptAuditManifestStore,
    head_store: TrustedDurableRunAuditHeadStore,
) -> TrustedDurableRunAuditHead:
    digest, count, latest = _snapshot(manifest_store)
    try:
        previous = head_store.load()
    except FileNotFoundError:
        previous = None
    if previous is not None:
        verification = verify_trusted_durable_run_audit_head(
            head=previous,
            manifest_store=manifest_store,
        )
        if verification.status is TrustedDurableRunAuditHeadStatus.CURRENT:
            return previous
        if (
            verification.status
            is not TrustedDurableRunAuditHeadStatus.ADVANCE_REQUIRED
        ):
            raise RuntimeError("trusted durable-run head cannot advance")
    payload = {
        "latest_audit_id": latest,
        "manifest_count": count,
        "manifest_store_hash": digest,
        "previous_anchor_id": (
            None if previous is None else previous.anchor_id
        ),
        "schema_version": _HEAD_SCHEMA,
    }
    head = TrustedDurableRunAuditHead(
        anchor_id=deterministic_id(
            "trusted_durable_run_audit_head",
            payload,
        ),
        **payload,
    )
    if head_store.save(head) != head.anchor_id or head_store.load() != head:
        raise RuntimeError("trusted durable-run head was not retained")
    return head


__all__ = [
    "TrustedDurableRunAuditHead",
    "TrustedDurableRunAuditHeadStatus",
    "TrustedDurableRunAuditHeadStore",
    "TrustedDurableRunAuditHeadVerification",
    "advance_trusted_durable_run_audit_head",
    "verify_trusted_durable_run_audit_head",
]
