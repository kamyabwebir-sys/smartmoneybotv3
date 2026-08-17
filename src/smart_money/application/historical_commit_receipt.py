from __future__ import annotations

import hmac
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from smart_money.application.commit_receipt_verification import (
    revalidate_commit_receipt,
)
from smart_money.application.durable_ingestion_commit import (
    ContentHashedEvidenceLedger,
    DurableIngestionCommitReceipt,
)
from smart_money.application.ports.market_state_checkpoint_store import (
    MarketStateCheckpointStore,
)
from smart_money.core.ids import deterministic_id
from smart_money.domain.market_state import (
    MarketStateCursor,
    make_market_state_checkpoint,
)

_SCHEMA_VERSION = "historical_commit_receipt.v1"
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_REASON_ORDER = (
    "current_state_matches",
    "evidence_missing",
    "checkpoint_missing",
    "ledger_prefix_missing",
    "evidence_corrupted",
    "checkpoint_anchor_mismatch",
    "checkpoint_binding_conflict",
    "current_cursor_behind",
    "ledger_checkpoint_drift",
    "historical_anchors_match",
)
_REASON_INDEX = {value: index for index, value in enumerate(_REASON_ORDER)}


class HistoricalCommitStatus(str, Enum):
    CURRENT = "CURRENT"
    HISTORICALLY_VALID = "HISTORICALLY_VALID"
    DRIFTED = "DRIFTED"
    MISSING = "MISSING"
    CORRUPTED = "CORRUPTED"
    CONFLICT = "CONFLICT"


@runtime_checkable
class HistoricalContentHashedEvidenceLedger(
    ContentHashedEvidenceLedger,
    Protocol,
):
    def contains_content_hash(self, content_hash: str) -> bool:
        """Return whether the digest identifies an append-only Ledger prefix."""
        ...


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
class HistoricalCommitAssessment:
    """Deterministic proof of a receipt against current or historical anchors."""

    assessment_id: str
    receipt_id: str
    status: HistoricalCommitStatus
    reason_codes: tuple[str, ...]
    ledger_anchor_found: bool
    checkpoint_anchor_matches: bool
    current_ledger_hash: str
    current_checkpoint_id: str | None
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "assessment_id",
            _require_text(self.assessment_id, "assessment_id"),
        )
        object.__setattr__(
            self,
            "receipt_id",
            _require_text(self.receipt_id, "receipt_id"),
        )
        if not isinstance(self.status, HistoricalCommitStatus):
            raise TypeError("status must be a HistoricalCommitStatus")
        if not isinstance(self.reason_codes, tuple):
            raise TypeError("reason_codes must be a tuple")
        unknown = set(self.reason_codes) - set(_REASON_ORDER)
        if unknown:
            raise ValueError("reason_codes contains unsupported values")
        normalized_reasons = tuple(
            sorted(set(self.reason_codes), key=_REASON_INDEX.__getitem__)
        )
        object.__setattr__(self, "reason_codes", normalized_reasons)
        for field_name in ("ledger_anchor_found", "checkpoint_anchor_matches"):
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(f"{field_name} must be a boolean")
        object.__setattr__(
            self,
            "current_ledger_hash",
            _require_sha256(
                self.current_ledger_hash,
                "current_ledger_hash",
            ),
        )
        if self.current_checkpoint_id is not None:
            object.__setattr__(
                self,
                "current_checkpoint_id",
                _require_text(
                    self.current_checkpoint_id,
                    "current_checkpoint_id",
                ),
            )
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported historical assessment schema_version")
        expected_id = deterministic_id(
            "historical_commit_assessment",
            self.identity_payload(),
        )
        if self.assessment_id != expected_id:
            raise ValueError("assessment_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, object]:
        return {
            "checkpoint_anchor_matches": self.checkpoint_anchor_matches,
            "current_checkpoint_id": self.current_checkpoint_id,
            "current_ledger_hash": self.current_ledger_hash,
            "ledger_anchor_found": self.ledger_anchor_found,
            "reason_codes": self.reason_codes,
            "receipt_id": self.receipt_id,
            "schema_version": self.schema_version,
            "status": self.status.value,
        }

    def canonical_dict(self) -> dict[str, object]:
        return {"assessment_id": self.assessment_id, **self.identity_payload()}


class HistoricalCommitAssessmentError(RuntimeError):
    def __init__(self, assessment: HistoricalCommitAssessment) -> None:
        self.assessment = assessment
        super().__init__(
            "historical commit receipt rejected: "
            f"{assessment.status.value} ({', '.join(assessment.reason_codes)})"
        )


def _make_assessment(
    *,
    receipt: DurableIngestionCommitReceipt,
    status: HistoricalCommitStatus,
    reasons: tuple[str, ...],
    ledger_anchor_found: bool,
    checkpoint_anchor_matches: bool,
    current_ledger_hash: str,
    current_checkpoint_id: str | None,
) -> HistoricalCommitAssessment:
    payload: dict[str, object] = {
        "checkpoint_anchor_matches": checkpoint_anchor_matches,
        "current_checkpoint_id": current_checkpoint_id,
        "current_ledger_hash": current_ledger_hash,
        "ledger_anchor_found": ledger_anchor_found,
        "reason_codes": tuple(
            sorted(set(reasons), key=_REASON_INDEX.__getitem__)
        ),
        "receipt_id": receipt.receipt_id,
        "schema_version": _SCHEMA_VERSION,
        "status": status.value,
    }
    return HistoricalCommitAssessment(
        assessment_id=deterministic_id(
            "historical_commit_assessment",
            payload,
        ),
        receipt_id=receipt.receipt_id,
        status=status,
        reason_codes=payload["reason_codes"],  # type: ignore[arg-type]
        ledger_anchor_found=ledger_anchor_found,
        checkpoint_anchor_matches=checkpoint_anchor_matches,
        current_ledger_hash=current_ledger_hash,
        current_checkpoint_id=current_checkpoint_id,
    )


def assess_historical_commit_receipt(
    *,
    receipt: DurableIngestionCommitReceipt,
    ledger: HistoricalContentHashedEvidenceLedger,
    checkpoint_store: MarketStateCheckpointStore,
) -> HistoricalCommitAssessment:
    if not isinstance(receipt, DurableIngestionCommitReceipt):
        raise TypeError("receipt must be a DurableIngestionCommitReceipt")
    if not isinstance(ledger, HistoricalContentHashedEvidenceLedger):
        raise TypeError("ledger must support historical content hashes")
    if not isinstance(checkpoint_store, MarketStateCheckpointStore):
        raise TypeError("checkpoint_store must satisfy its application port")

    current_hash = _require_sha256(ledger.content_hash, "ledger.content_hash")
    current = revalidate_commit_receipt(
        receipt=receipt,
        ledger=ledger,
        checkpoint_store=checkpoint_store,
    )
    if current.valid:
        return _make_assessment(
            receipt=receipt,
            status=HistoricalCommitStatus.CURRENT,
            reasons=("current_state_matches",),
            ledger_anchor_found=True,
            checkpoint_anchor_matches=True,
            current_ledger_hash=current_hash,
            current_checkpoint_id=current.persisted_checkpoint_id,
        )

    ledger_anchor_found = ledger.contains_content_hash(
        receipt.ledger_content_hash
    )
    evidence = ledger.get(receipt.evidence_id)
    try:
        checkpoint = checkpoint_store.load()
    except FileNotFoundError:
        checkpoint = None

    if evidence is None or checkpoint is None:
        reasons = (
            ("evidence_missing",) if evidence is None else ()
        ) + (("checkpoint_missing",) if checkpoint is None else ())
        return _make_assessment(
            receipt=receipt,
            status=HistoricalCommitStatus.MISSING,
            reasons=reasons,
            ledger_anchor_found=ledger_anchor_found,
            checkpoint_anchor_matches=False,
            current_ledger_hash=current_hash,
            current_checkpoint_id=(
                None if checkpoint is None else checkpoint.checkpoint_id
            ),
        )

    if (
        checkpoint.provider_id != receipt.provider_id
        or checkpoint.market.canonical_id != receipt.market_id
    ):
        return _make_assessment(
            receipt=receipt,
            status=HistoricalCommitStatus.CONFLICT,
            reasons=("checkpoint_binding_conflict",),
            ledger_anchor_found=ledger_anchor_found,
            checkpoint_anchor_matches=False,
            current_ledger_hash=current_hash,
            current_checkpoint_id=checkpoint.checkpoint_id,
        )

    state_change = evidence.data.get("market_state_change")
    provenance = evidence.metadata.get("provenance")
    evidence_corrupted = (
        evidence.evidence_type != "canonical_market_state_observation"
        or evidence.source_id != receipt.provider_id
        or not isinstance(state_change, Mapping)
        or not isinstance(provenance, Mapping)
    )
    if not evidence_corrupted:
        chain_sequence = state_change.get("chain_sequence")
        event_index = state_change.get("event_index")
        evidence_corrupted = (
            isinstance(chain_sequence, bool)
            or not isinstance(chain_sequence, int)
            or isinstance(event_index, bool)
            or not isinstance(event_index, int)
            or state_change.get("event_id") != receipt.event_id
            or state_change.get("source_event_id") != receipt.source_event_id
            or provenance.get("source_id") != receipt.provider_id
            or provenance.get("source_event_id") != receipt.source_event_id
            or provenance.get("market_id") != receipt.market_id
        )
    if evidence_corrupted:
        return _make_assessment(
            receipt=receipt,
            status=HistoricalCommitStatus.CORRUPTED,
            reasons=("evidence_corrupted",),
            ledger_anchor_found=ledger_anchor_found,
            checkpoint_anchor_matches=False,
            current_ledger_hash=current_hash,
            current_checkpoint_id=checkpoint.checkpoint_id,
        )

    assert isinstance(state_change, Mapping)
    chain_sequence = state_change["chain_sequence"]
    event_index = state_change["event_index"]
    assert isinstance(chain_sequence, int)
    assert isinstance(event_index, int)
    historical_cursor = MarketStateCursor(
        provider_id=receipt.provider_id,
        chain=checkpoint.chain,
        chain_sequence=chain_sequence,
        event_index=event_index,
    )
    historical_checkpoint = make_market_state_checkpoint(
        provider_id=receipt.provider_id,
        chain=checkpoint.chain,
        market=checkpoint.market,
        cursor=historical_cursor,
        reorder_window_blocks=checkpoint.reorder_window_blocks,
    )
    checkpoint_anchor_matches = hmac.compare_digest(
        historical_checkpoint.checkpoint_id,
        receipt.checkpoint_id,
    )
    if not ledger_anchor_found or not checkpoint_anchor_matches:
        reasons = (
            ("ledger_prefix_missing",) if not ledger_anchor_found else ()
        ) + (
            ("checkpoint_anchor_mismatch",)
            if not checkpoint_anchor_matches
            else ()
        )
        return _make_assessment(
            receipt=receipt,
            status=HistoricalCommitStatus.CORRUPTED,
            reasons=reasons,
            ledger_anchor_found=ledger_anchor_found,
            checkpoint_anchor_matches=checkpoint_anchor_matches,
            current_ledger_hash=current_hash,
            current_checkpoint_id=checkpoint.checkpoint_id,
        )

    if checkpoint.cursor.ordering_key < historical_cursor.ordering_key:
        return _make_assessment(
            receipt=receipt,
            status=HistoricalCommitStatus.CONFLICT,
            reasons=("current_cursor_behind",),
            ledger_anchor_found=True,
            checkpoint_anchor_matches=True,
            current_ledger_hash=current_hash,
            current_checkpoint_id=checkpoint.checkpoint_id,
        )

    ledger_advanced = not hmac.compare_digest(
        current_hash,
        receipt.ledger_content_hash,
    )
    checkpoint_advanced = (
        checkpoint.cursor.ordering_key > historical_cursor.ordering_key
    )
    if ledger_advanced and checkpoint_advanced:
        return _make_assessment(
            receipt=receipt,
            status=HistoricalCommitStatus.HISTORICALLY_VALID,
            reasons=("historical_anchors_match",),
            ledger_anchor_found=True,
            checkpoint_anchor_matches=True,
            current_ledger_hash=current_hash,
            current_checkpoint_id=checkpoint.checkpoint_id,
        )
    return _make_assessment(
        receipt=receipt,
        status=HistoricalCommitStatus.DRIFTED,
        reasons=("ledger_checkpoint_drift",),
        ledger_anchor_found=True,
        checkpoint_anchor_matches=True,
        current_ledger_hash=current_hash,
        current_checkpoint_id=checkpoint.checkpoint_id,
    )


def verify_historical_commit_receipt_or_raise(
    *,
    receipt: DurableIngestionCommitReceipt,
    ledger: HistoricalContentHashedEvidenceLedger,
    checkpoint_store: MarketStateCheckpointStore,
) -> HistoricalCommitAssessment:
    assessment = assess_historical_commit_receipt(
        receipt=receipt,
        ledger=ledger,
        checkpoint_store=checkpoint_store,
    )
    if assessment.status not in {
        HistoricalCommitStatus.CURRENT,
        HistoricalCommitStatus.HISTORICALLY_VALID,
    }:
        raise HistoricalCommitAssessmentError(assessment)
    return assessment


__all__ = [
    "HistoricalCommitAssessment",
    "HistoricalCommitAssessmentError",
    "HistoricalCommitStatus",
    "HistoricalContentHashedEvidenceLedger",
    "assess_historical_commit_receipt",
    "verify_historical_commit_receipt_or_raise",
]
