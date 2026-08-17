from __future__ import annotations

import hmac
import re
from dataclasses import dataclass

from smart_money.application.historical_commit_receipt import (
    HistoricalCommitStatus,
    HistoricalContentHashedEvidenceLedger,
    assess_historical_commit_receipt,
)
from smart_money.application.ports.commit_receipt_store import (
    CommitReceiptStore,
)
from smart_money.application.ports.market_state_checkpoint_store import (
    MarketStateCheckpointStore,
)
from smart_money.core.ids import deterministic_id
from smart_money.domain.market_state import MarketStateCheckpoint

_SCHEMA_VERSION = "historical_receipt_audit.v1"
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_ACCEPTED_STATUSES = frozenset(
    {
        HistoricalCommitStatus.CURRENT,
        HistoricalCommitStatus.HISTORICALLY_VALID,
    }
)


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


def _require_count(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


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
class HistoricalReceiptAuditManifest:
    """Content-addressed summary of one stable historical receipt sweep."""

    audit_id: str
    receipt_store_hash: str
    ledger_content_hash: str
    receipt_count: int
    current_count: int
    historically_valid_count: int
    drifted_count: int
    missing_count: int
    corrupted_count: int
    conflict_count: int
    assessment_ids: tuple[str, ...]
    rejected_receipt_ids: tuple[str, ...]
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
        count_fields = (
            "receipt_count",
            "current_count",
            "historically_valid_count",
            "drifted_count",
            "missing_count",
            "corrupted_count",
            "conflict_count",
        )
        for field_name in count_fields:
            object.__setattr__(
                self,
                field_name,
                _require_count(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "assessment_ids",
            _normalize_ids(self.assessment_ids, "assessment_ids"),
        )
        object.__setattr__(
            self,
            "rejected_receipt_ids",
            _normalize_ids(
                self.rejected_receipt_ids,
                "rejected_receipt_ids",
            ),
        )
        status_total = (
            self.current_count
            + self.historically_valid_count
            + self.drifted_count
            + self.missing_count
            + self.corrupted_count
            + self.conflict_count
        )
        if status_total != self.receipt_count:
            raise ValueError("status counts must equal receipt_count")
        if len(self.assessment_ids) != self.receipt_count:
            raise ValueError("assessment_ids must match receipt_count")
        if len(self.rejected_receipt_ids) != self.rejected_count:
            raise ValueError("rejected_receipt_ids must match rejected_count")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError(
                "unsupported historical receipt audit schema_version"
            )
        expected_id = deterministic_id(
            "historical_receipt_audit",
            self.identity_payload(),
        )
        if self.audit_id != expected_id:
            raise ValueError("audit_id does not match deterministic payload")

    @property
    def accepted_count(self) -> int:
        return self.current_count + self.historically_valid_count

    @property
    def rejected_count(self) -> int:
        return (
            self.drifted_count
            + self.missing_count
            + self.corrupted_count
            + self.conflict_count
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "assessment_ids": self.assessment_ids,
            "conflict_count": self.conflict_count,
            "corrupted_count": self.corrupted_count,
            "current_count": self.current_count,
            "drifted_count": self.drifted_count,
            "historically_valid_count": self.historically_valid_count,
            "ledger_content_hash": self.ledger_content_hash,
            "missing_count": self.missing_count,
            "receipt_count": self.receipt_count,
            "receipt_store_hash": self.receipt_store_hash,
            "rejected_receipt_ids": self.rejected_receipt_ids,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, object]:
        return {"audit_id": self.audit_id, **self.identity_payload()}


class HistoricalReceiptAuditError(RuntimeError):
    def __init__(self, manifest: HistoricalReceiptAuditManifest) -> None:
        self.manifest = manifest
        super().__init__(
            "historical receipt audit rejected receipts: "
            f"{', '.join(manifest.rejected_receipt_ids)}"
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


def _load_checkpoint(
    checkpoint_store: MarketStateCheckpointStore,
) -> MarketStateCheckpoint | None:
    try:
        return checkpoint_store.load()
    except FileNotFoundError:
        return None


def audit_historical_receipts(
    *,
    receipt_store: CommitReceiptStore,
    ledger: HistoricalContentHashedEvidenceLedger,
    checkpoint_store: MarketStateCheckpointStore,
) -> HistoricalReceiptAuditManifest:
    if not isinstance(receipt_store, CommitReceiptStore):
        raise TypeError("receipt_store must satisfy CommitReceiptStore")
    if not isinstance(ledger, HistoricalContentHashedEvidenceLedger):
        raise TypeError("ledger must support historical content hashes")
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
    if len({receipt.receipt_id for receipt in receipts}) != receipt_count:
        raise RuntimeError("receipt store snapshot contains duplicate identities")
    for receipt in receipts:
        if receipt_store.get(receipt.receipt_id) != receipt:
            raise RuntimeError("receipt store lookup disagrees with iteration")

    checkpoint = _load_checkpoint(checkpoint_store) if receipts else None
    snapshot = _CheckpointSnapshot(checkpoint)
    assessments = tuple(
        assess_historical_commit_receipt(
            receipt=receipt,
            ledger=ledger,
            checkpoint_store=snapshot,
        )
        for receipt in receipts
    )

    if receipt_store.receipt_count != receipt_count or not hmac.compare_digest(
        receipt_store.content_hash,
        receipt_store_hash,
    ):
        raise RuntimeError("receipt store changed during historical audit")
    if not hmac.compare_digest(ledger.content_hash, ledger_hash):
        raise RuntimeError("Ledger changed during historical audit")
    if receipts and _load_checkpoint(checkpoint_store) != checkpoint:
        raise RuntimeError("checkpoint changed during historical audit")

    counts = {
        status: sum(
            assessment.status is status for assessment in assessments
        )
        for status in HistoricalCommitStatus
    }
    rejected_receipt_ids = tuple(
        receipt.receipt_id
        for receipt, assessment in zip(receipts, assessments, strict=True)
        if assessment.status not in _ACCEPTED_STATUSES
    )
    payload: dict[str, object] = {
        "assessment_ids": tuple(
            assessment.assessment_id for assessment in assessments
        ),
        "conflict_count": counts[HistoricalCommitStatus.CONFLICT],
        "corrupted_count": counts[HistoricalCommitStatus.CORRUPTED],
        "current_count": counts[HistoricalCommitStatus.CURRENT],
        "drifted_count": counts[HistoricalCommitStatus.DRIFTED],
        "historically_valid_count": counts[
            HistoricalCommitStatus.HISTORICALLY_VALID
        ],
        "ledger_content_hash": ledger_hash,
        "missing_count": counts[HistoricalCommitStatus.MISSING],
        "receipt_count": receipt_count,
        "receipt_store_hash": receipt_store_hash,
        "rejected_receipt_ids": rejected_receipt_ids,
        "schema_version": _SCHEMA_VERSION,
    }
    return HistoricalReceiptAuditManifest(
        audit_id=deterministic_id("historical_receipt_audit", payload),
        receipt_store_hash=receipt_store_hash,
        ledger_content_hash=ledger_hash,
        receipt_count=receipt_count,
        current_count=counts[HistoricalCommitStatus.CURRENT],
        historically_valid_count=counts[
            HistoricalCommitStatus.HISTORICALLY_VALID
        ],
        drifted_count=counts[HistoricalCommitStatus.DRIFTED],
        missing_count=counts[HistoricalCommitStatus.MISSING],
        corrupted_count=counts[HistoricalCommitStatus.CORRUPTED],
        conflict_count=counts[HistoricalCommitStatus.CONFLICT],
        assessment_ids=payload["assessment_ids"],  # type: ignore[arg-type]
        rejected_receipt_ids=rejected_receipt_ids,
    )


def audit_historical_receipts_or_raise(
    *,
    receipt_store: CommitReceiptStore,
    ledger: HistoricalContentHashedEvidenceLedger,
    checkpoint_store: MarketStateCheckpointStore,
) -> HistoricalReceiptAuditManifest:
    manifest = audit_historical_receipts(
        receipt_store=receipt_store,
        ledger=ledger,
        checkpoint_store=checkpoint_store,
    )
    if manifest.rejected_count:
        raise HistoricalReceiptAuditError(manifest)
    return manifest


__all__ = [
    "HistoricalReceiptAuditError",
    "HistoricalReceiptAuditManifest",
    "audit_historical_receipts",
    "audit_historical_receipts_or_raise",
]
