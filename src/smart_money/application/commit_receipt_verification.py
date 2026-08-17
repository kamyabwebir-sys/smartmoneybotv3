from __future__ import annotations

import hmac
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from smart_money.application.durable_ingestion_commit import (
    ContentHashedEvidenceLedger,
    DurableIngestionCommitReceipt,
)
from smart_money.application.ports.market_state_checkpoint_store import (
    MarketStateCheckpointStore,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "commit_receipt_verification.v1"
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_MISMATCH_ORDER = (
    "ledger_content_hash",
    "evidence_missing",
    "evidence_type",
    "evidence_payload",
    "evidence_event_id",
    "evidence_source_event_id",
    "evidence_provider_id",
    "evidence_market_id",
    "checkpoint_missing",
    "checkpoint_id",
    "checkpoint_provider_id",
    "checkpoint_market_id",
    "checkpoint_cursor",
)
_MISMATCH_INDEX = {
    field_name: index for index, field_name in enumerate(_MISMATCH_ORDER)
}


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


@dataclass(frozen=True, slots=True)
class CommitReceiptVerification:
    """Deterministic comparison of a receipt with current durable state."""

    verification_id: str
    receipt_id: str
    valid: bool
    mismatch_fields: tuple[str, ...]
    current_ledger_hash: str
    persisted_checkpoint_id: str | None
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "verification_id",
            _require_text(self.verification_id, "verification_id"),
        )
        object.__setattr__(
            self,
            "receipt_id",
            _require_text(self.receipt_id, "receipt_id"),
        )
        if not isinstance(self.valid, bool):
            raise TypeError("valid must be a boolean")
        if not isinstance(self.mismatch_fields, tuple):
            raise TypeError("mismatch_fields must be a tuple")
        unknown_fields = set(self.mismatch_fields) - set(_MISMATCH_ORDER)
        if unknown_fields:
            raise ValueError("mismatch_fields contains unsupported values")
        normalized_fields = tuple(
            sorted(
                set(self.mismatch_fields),
                key=_MISMATCH_INDEX.__getitem__,
            )
        )
        object.__setattr__(self, "mismatch_fields", normalized_fields)
        if self.valid != (not normalized_fields):
            raise ValueError("valid must agree with mismatch_fields")
        object.__setattr__(
            self,
            "current_ledger_hash",
            _require_sha256(
                self.current_ledger_hash,
                "current_ledger_hash",
            ),
        )
        if self.persisted_checkpoint_id is not None:
            object.__setattr__(
                self,
                "persisted_checkpoint_id",
                _require_text(
                    self.persisted_checkpoint_id,
                    "persisted_checkpoint_id",
                ),
            )
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError(
                "unsupported commit receipt verification schema_version"
            )
        expected_id = deterministic_id(
            "commit_receipt_verification",
            self.identity_payload(),
        )
        if self.verification_id != expected_id:
            raise ValueError("verification_id does not match deterministic payload")

    def identity_payload(
        self,
    ) -> dict[str, str | bool | tuple[str, ...] | None]:
        return {
            "current_ledger_hash": self.current_ledger_hash,
            "mismatch_fields": self.mismatch_fields,
            "persisted_checkpoint_id": self.persisted_checkpoint_id,
            "receipt_id": self.receipt_id,
            "schema_version": self.schema_version,
            "valid": self.valid,
        }

    def canonical_dict(
        self,
    ) -> dict[str, str | bool | tuple[str, ...] | None]:
        return {
            "verification_id": self.verification_id,
            **self.identity_payload(),
        }


class CommitReceiptVerificationError(RuntimeError):
    """Raised when strict revalidation finds any durable-state mismatch."""

    def __init__(self, verification: CommitReceiptVerification) -> None:
        self.verification = verification
        mismatches = ", ".join(verification.mismatch_fields)
        super().__init__(f"commit receipt verification mismatch: {mismatches}")


def revalidate_commit_receipt(
    *,
    receipt: DurableIngestionCommitReceipt,
    ledger: ContentHashedEvidenceLedger,
    checkpoint_store: MarketStateCheckpointStore,
) -> CommitReceiptVerification:
    if not isinstance(receipt, DurableIngestionCommitReceipt):
        raise TypeError("receipt must be a DurableIngestionCommitReceipt")
    if not isinstance(ledger, ContentHashedEvidenceLedger):
        raise TypeError("ledger must provide EvidenceLedger and content_hash")
    if not isinstance(checkpoint_store, MarketStateCheckpointStore):
        raise TypeError("checkpoint_store must satisfy its application port")

    current_hash = _require_sha256(ledger.content_hash, "ledger.content_hash")
    mismatches: list[str] = []
    if not hmac.compare_digest(current_hash, receipt.ledger_content_hash):
        mismatches.append("ledger_content_hash")

    evidence = ledger.get(receipt.evidence_id)
    state_change: Mapping[str, Any] | None = None
    if evidence is None:
        mismatches.append("evidence_missing")
    else:
        if evidence.evidence_type != "canonical_market_state_observation":
            mismatches.append("evidence_type")
        raw_state_change = evidence.data.get("market_state_change")
        if not isinstance(raw_state_change, Mapping):
            mismatches.append("evidence_payload")
        else:
            state_change = raw_state_change
            if state_change.get("event_id") != receipt.event_id:
                mismatches.append("evidence_event_id")
            if (
                state_change.get("source_event_id")
                != receipt.source_event_id
            ):
                mismatches.append("evidence_source_event_id")
        provenance = evidence.metadata.get("provenance")
        if evidence.source_id != receipt.provider_id:
            mismatches.append("evidence_provider_id")
        if not isinstance(provenance, Mapping):
            mismatches.append("evidence_payload")
        else:
            if provenance.get("source_id") != receipt.provider_id:
                mismatches.append("evidence_provider_id")
            if provenance.get("source_event_id") != receipt.source_event_id:
                mismatches.append("evidence_source_event_id")
            if provenance.get("market_id") != receipt.market_id:
                mismatches.append("evidence_market_id")

    try:
        checkpoint = checkpoint_store.load()
    except FileNotFoundError:
        checkpoint = None
        mismatches.append("checkpoint_missing")

    persisted_checkpoint_id: str | None = None
    if checkpoint is not None:
        persisted_checkpoint_id = checkpoint.checkpoint_id
        if checkpoint.checkpoint_id != receipt.checkpoint_id:
            mismatches.append("checkpoint_id")
        if checkpoint.provider_id != receipt.provider_id:
            mismatches.append("checkpoint_provider_id")
        if checkpoint.market.canonical_id != receipt.market_id:
            mismatches.append("checkpoint_market_id")
        if state_change is not None:
            expected_cursor = (
                state_change.get("chain_sequence"),
                state_change.get("event_index"),
            )
            if checkpoint.cursor.ordering_key != expected_cursor:
                mismatches.append("checkpoint_cursor")

    normalized_fields = tuple(
        sorted(set(mismatches), key=_MISMATCH_INDEX.__getitem__)
    )
    payload: dict[str, str | bool | tuple[str, ...] | None] = {
        "current_ledger_hash": current_hash,
        "mismatch_fields": normalized_fields,
        "persisted_checkpoint_id": persisted_checkpoint_id,
        "receipt_id": receipt.receipt_id,
        "schema_version": _SCHEMA_VERSION,
        "valid": not normalized_fields,
    }
    return CommitReceiptVerification(
        verification_id=deterministic_id(
            "commit_receipt_verification",
            payload,
        ),
        receipt_id=receipt.receipt_id,
        valid=not normalized_fields,
        mismatch_fields=normalized_fields,
        current_ledger_hash=current_hash,
        persisted_checkpoint_id=persisted_checkpoint_id,
    )


def verify_commit_receipt_or_raise(
    *,
    receipt: DurableIngestionCommitReceipt,
    ledger: ContentHashedEvidenceLedger,
    checkpoint_store: MarketStateCheckpointStore,
) -> CommitReceiptVerification:
    verification = revalidate_commit_receipt(
        receipt=receipt,
        ledger=ledger,
        checkpoint_store=checkpoint_store,
    )
    if not verification.valid:
        raise CommitReceiptVerificationError(verification)
    return verification


__all__ = [
    "CommitReceiptVerification",
    "CommitReceiptVerificationError",
    "revalidate_commit_receipt",
    "verify_commit_receipt_or_raise",
]
