from __future__ import annotations

import hmac
import re
from dataclasses import dataclass

from smart_money.application.commit_receipt_verification import (
    revalidate_commit_receipt,
)
from smart_money.application.durable_ingestion_commit import (
    ContentHashedEvidenceLedger,
)
from smart_money.application.ports.commit_receipt_store import (
    CommitReceiptStore,
)
from smart_money.application.ports.market_state_checkpoint_store import (
    MarketStateCheckpointStore,
)
from smart_money.core.ids import deterministic_id
from smart_money.domain.market_state import MarketStateCheckpoint

_SCHEMA_VERSION = "commit_receipt_audit.v1"
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _require_sha256(value: object, field_name: str) -> str:
    digest = _require_text(value, field_name)
    if _SHA256_PATTERN.fullmatch(digest) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 hex digest")
    return digest


def _normalize_ids(
    values: tuple[str, ...],
    field_name: str,
) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    normalized = tuple(_require_text(value, field_name) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must contain unique identities")
    return normalized


@dataclass(frozen=True, slots=True)
class CommitReceiptAuditManifest:
    """Content-addressed result of one stable receipt-store audit sweep."""

    audit_id: str
    receipt_store_hash: str
    ledger_content_hash: str
    receipt_count: int
    valid_count: int
    invalid_count: int
    verification_ids: tuple[str, ...]
    invalid_receipt_ids: tuple[str, ...]
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "audit_id",
            _require_text(self.audit_id, "audit_id"),
        )
        object.__setattr__(
            self,
            "receipt_store_hash",
            _require_sha256(
                self.receipt_store_hash,
                "receipt_store_hash",
            ),
        )
        object.__setattr__(
            self,
            "ledger_content_hash",
            _require_sha256(
                self.ledger_content_hash,
                "ledger_content_hash",
            ),
        )
        for field_name in ("receipt_count", "valid_count", "invalid_count"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field_name} must be an integer")
            if value < 0:
                raise ValueError(f"{field_name} must be non-negative")
        object.__setattr__(
            self,
            "verification_ids",
            _normalize_ids(self.verification_ids, "verification_ids"),
        )
        object.__setattr__(
            self,
            "invalid_receipt_ids",
            _normalize_ids(
                self.invalid_receipt_ids,
                "invalid_receipt_ids",
            ),
        )
        if self.valid_count + self.invalid_count != self.receipt_count:
            raise ValueError("valid and invalid counts must equal receipt_count")
        if len(self.verification_ids) != self.receipt_count:
            raise ValueError("verification_ids must match receipt_count")
        if len(self.invalid_receipt_ids) != self.invalid_count:
            raise ValueError("invalid_receipt_ids must match invalid_count")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported commit receipt audit schema_version")
        expected_id = deterministic_id(
            "commit_receipt_audit",
            self.identity_payload(),
        )
        if self.audit_id != expected_id:
            raise ValueError("audit_id does not match deterministic payload")

    def identity_payload(
        self,
    ) -> dict[str, str | int | tuple[str, ...]]:
        return {
            "invalid_count": self.invalid_count,
            "invalid_receipt_ids": self.invalid_receipt_ids,
            "ledger_content_hash": self.ledger_content_hash,
            "receipt_count": self.receipt_count,
            "receipt_store_hash": self.receipt_store_hash,
            "schema_version": self.schema_version,
            "valid_count": self.valid_count,
            "verification_ids": self.verification_ids,
        }

    def canonical_dict(
        self,
    ) -> dict[str, str | int | tuple[str, ...]]:
        return {"audit_id": self.audit_id, **self.identity_payload()}


class CommitReceiptAuditError(RuntimeError):
    """Raised when strict audit finds any invalid commit receipt."""

    def __init__(self, manifest: CommitReceiptAuditManifest) -> None:
        self.manifest = manifest
        super().__init__(
            "commit receipt audit found invalid receipts: "
            f"{', '.join(manifest.invalid_receipt_ids)}"
        )


@dataclass(slots=True)
class _CheckpointSnapshot:
    checkpoint: MarketStateCheckpoint | None

    def load(self) -> MarketStateCheckpoint:
        if self.checkpoint is None:
            raise FileNotFoundError("checkpoint missing in audit snapshot")
        return self.checkpoint

    def save(self, checkpoint: MarketStateCheckpoint) -> None:
        raise RuntimeError("audit checkpoint snapshot is read-only")


def audit_commit_receipts(
    *,
    receipt_store: CommitReceiptStore,
    ledger: ContentHashedEvidenceLedger,
    checkpoint_store: MarketStateCheckpointStore,
) -> CommitReceiptAuditManifest:
    if not isinstance(receipt_store, CommitReceiptStore):
        raise TypeError("receipt_store must satisfy CommitReceiptStore")
    if not isinstance(ledger, ContentHashedEvidenceLedger):
        raise TypeError("ledger must provide EvidenceLedger and content_hash")
    if not isinstance(checkpoint_store, MarketStateCheckpointStore):
        raise TypeError("checkpoint_store must satisfy its application port")

    receipt_store_hash = _require_sha256(
        receipt_store.content_hash,
        "receipt_store.content_hash",
    )
    ledger_hash = _require_sha256(
        ledger.content_hash,
        "ledger.content_hash",
    )
    receipt_count = receipt_store.receipt_count
    receipts = tuple(receipt_store.iter_receipts())
    if len(receipts) != receipt_count:
        raise RuntimeError("receipt store count changed before audit snapshot")
    if len({receipt.receipt_id for receipt in receipts}) != len(receipts):
        raise RuntimeError("receipt store snapshot contains duplicate identities")
    for receipt in receipts:
        if receipt_store.get(receipt.receipt_id) != receipt:
            raise RuntimeError("receipt store lookup disagrees with iteration")

    checkpoint: MarketStateCheckpoint | None = None
    if receipts:
        try:
            checkpoint = checkpoint_store.load()
        except FileNotFoundError:
            checkpoint = None
    checkpoint_snapshot = _CheckpointSnapshot(checkpoint)

    verifications = tuple(
        revalidate_commit_receipt(
            receipt=receipt,
            ledger=ledger,
            checkpoint_store=checkpoint_snapshot,
        )
        for receipt in receipts
    )
    if receipt_store.receipt_count != receipt_count or not hmac.compare_digest(
        receipt_store.content_hash,
        receipt_store_hash,
    ):
        raise RuntimeError("receipt store changed during audit sweep")
    if not hmac.compare_digest(ledger.content_hash, ledger_hash):
        raise RuntimeError("Ledger changed during audit sweep")

    invalid_receipt_ids = tuple(
        receipt.receipt_id
        for receipt, verification in zip(receipts, verifications, strict=True)
        if not verification.valid
    )
    payload: dict[str, str | int | tuple[str, ...]] = {
        "invalid_count": len(invalid_receipt_ids),
        "invalid_receipt_ids": invalid_receipt_ids,
        "ledger_content_hash": ledger_hash,
        "receipt_count": receipt_count,
        "receipt_store_hash": receipt_store_hash,
        "schema_version": _SCHEMA_VERSION,
        "valid_count": receipt_count - len(invalid_receipt_ids),
        "verification_ids": tuple(
            verification.verification_id for verification in verifications
        ),
    }
    return CommitReceiptAuditManifest(
        audit_id=deterministic_id("commit_receipt_audit", payload),
        receipt_store_hash=receipt_store_hash,
        ledger_content_hash=ledger_hash,
        receipt_count=receipt_count,
        valid_count=payload["valid_count"],
        invalid_count=payload["invalid_count"],
        verification_ids=payload["verification_ids"],
        invalid_receipt_ids=invalid_receipt_ids,
    )


def audit_commit_receipts_or_raise(
    *,
    receipt_store: CommitReceiptStore,
    ledger: ContentHashedEvidenceLedger,
    checkpoint_store: MarketStateCheckpointStore,
) -> CommitReceiptAuditManifest:
    manifest = audit_commit_receipts(
        receipt_store=receipt_store,
        ledger=ledger,
        checkpoint_store=checkpoint_store,
    )
    if manifest.invalid_count:
        raise CommitReceiptAuditError(manifest)
    return manifest


__all__ = [
    "CommitReceiptAuditError",
    "CommitReceiptAuditManifest",
    "audit_commit_receipts",
    "audit_commit_receipts_or_raise",
]
