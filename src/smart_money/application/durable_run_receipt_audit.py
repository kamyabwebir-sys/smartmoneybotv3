from __future__ import annotations

import hmac
from dataclasses import dataclass
from enum import Enum

from smart_money.application._validation import (
    assert_stable_collection_snapshot,
    take_stable_collection_snapshot,
)
from smart_money.application._validation import (
    require_count as _require_count,
)
from smart_money.application._validation import (
    require_sha256 as _require_sha256,
)
from smart_money.application._validation import (
    require_text as _require_text,
)
from smart_money.application.durable_ingestion_commit import (
    DurableIngestionCommitReceipt,
)
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
from smart_money.application.ports.recovery_gated_run_store import (
    RecoveryGatedRunStore,
)
from smart_money.application.recovery_gated_ingestion import (
    RecoveryGatedIngestionResult,
)
from smart_money.application.trusted_audit_head import (
    PrefixVerifiableHistoricalAuditStore,
    TrustedAuditHeadStatus,
)
from smart_money.core.ids import deterministic_id

_ASSESSMENT_SCHEMA_VERSION = "durable_run_receipt_assessment.v1"
_MANIFEST_SCHEMA_VERSION = "durable_run_receipt_audit.v1"
_VERIFICATION_SCHEMA_VERSION = "trusted_audit_head_verification.v1"
class DurableRunReceiptStatus(str, Enum):
    CURRENT = "CURRENT"
    HISTORICALLY_VALID = "HISTORICALLY_VALID"
    MISSING_PREFIX = "MISSING_PREFIX"
    CONFLICT = "CONFLICT"


_ACCEPTED_STATUSES = frozenset(
    {
        DurableRunReceiptStatus.CURRENT,
        DurableRunReceiptStatus.HISTORICALLY_VALID,
    }
)
_ACCEPTED_COMMIT_STATUSES = frozenset(
    {
        HistoricalCommitStatus.CURRENT,
        HistoricalCommitStatus.HISTORICALLY_VALID,
    }
)


@dataclass(frozen=True, slots=True)
class DurableRunReceiptAssessment:
    """Deterministic validation of one persisted recovery-gated run."""

    assessment_id: str
    run_id: str
    gate_decision_id: str
    ingestion_session_id: str
    trusted_anchor_id: str
    verification_id: str
    referenced_manifest_hash: str
    referenced_manifest_count: int
    referenced_latest_audit_id: str | None
    commit_receipt_id: str | None
    commit_assessment_id: str | None
    commit_status: HistoricalCommitStatus | None
    status: DurableRunReceiptStatus
    schema_version: str = _ASSESSMENT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "assessment_id",
            "run_id",
            "gate_decision_id",
            "ingestion_session_id",
            "trusted_anchor_id",
            "verification_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "referenced_manifest_hash",
            _require_sha256(
                self.referenced_manifest_hash,
                "referenced_manifest_hash",
            ),
        )
        object.__setattr__(
            self,
            "referenced_manifest_count",
            _require_count(
                self.referenced_manifest_count,
                "referenced_manifest_count",
            ),
        )
        if self.referenced_latest_audit_id is not None:
            object.__setattr__(
                self,
                "referenced_latest_audit_id",
                _require_text(
                    self.referenced_latest_audit_id,
                    "referenced_latest_audit_id",
                ),
            )
        if (self.referenced_manifest_count == 0) != (
            self.referenced_latest_audit_id is None
        ):
            raise ValueError(
                "referenced latest audit presence must agree with count"
            )
        for field_name in ("commit_receipt_id", "commit_assessment_id"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _require_text(value, field_name),
                )
        commit_fields_present = (
            self.commit_receipt_id is not None,
            self.commit_assessment_id is not None,
            self.commit_status is not None,
        )
        if len(set(commit_fields_present)) != 1:
            raise ValueError(
                "commit receipt, assessment, and status must be present together"
            )
        if (
            self.commit_status is not None
            and not isinstance(self.commit_status, HistoricalCommitStatus)
        ):
            raise TypeError("commit_status must be a HistoricalCommitStatus")
        if not isinstance(self.status, DurableRunReceiptStatus):
            raise TypeError("status must be a DurableRunReceiptStatus")
        if self.schema_version != _ASSESSMENT_SCHEMA_VERSION:
            raise ValueError(
                "unsupported durable run receipt assessment schema_version"
            )
        expected_id = deterministic_id(
            "durable_run_receipt_assessment",
            self.identity_payload(),
        )
        if self.assessment_id != expected_id:
            raise ValueError(
                "assessment_id does not match deterministic payload"
            )

    @property
    def accepted(self) -> bool:
        return self.status in _ACCEPTED_STATUSES

    def identity_payload(self) -> dict[str, object]:
        return {
            "commit_assessment_id": self.commit_assessment_id,
            "commit_receipt_id": self.commit_receipt_id,
            "commit_status": (
                None if self.commit_status is None else self.commit_status.value
            ),
            "gate_decision_id": self.gate_decision_id,
            "ingestion_session_id": self.ingestion_session_id,
            "referenced_latest_audit_id": self.referenced_latest_audit_id,
            "referenced_manifest_count": self.referenced_manifest_count,
            "referenced_manifest_hash": self.referenced_manifest_hash,
            "run_id": self.run_id,
            "schema_version": self.schema_version,
            "status": self.status.value,
            "trusted_anchor_id": self.trusted_anchor_id,
            "verification_id": self.verification_id,
        }

    def canonical_dict(self) -> dict[str, object]:
        return {"assessment_id": self.assessment_id, **self.identity_payload()}


@dataclass(frozen=True, slots=True)
class DurableRunReceiptAuditManifest:
    """Content-addressed summary of a stable durable-run audit sweep."""

    audit_id: str
    run_store_hash: str
    manifest_store_hash: str
    commit_receipt_store_hash: str
    ledger_content_hash: str
    checkpoint_id: str | None
    manifest_count: int
    commit_receipt_count: int
    run_count: int
    current_count: int
    historically_valid_count: int
    missing_prefix_count: int
    conflict_count: int
    assessments: tuple[DurableRunReceiptAssessment, ...]
    rejected_run_ids: tuple[str, ...]
    schema_version: str = _MANIFEST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "audit_id",
            _require_text(self.audit_id, "audit_id"),
        )
        for field_name in (
            "run_store_hash",
            "manifest_store_hash",
            "commit_receipt_store_hash",
            "ledger_content_hash",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_sha256(getattr(self, field_name), field_name),
            )
        if self.checkpoint_id is not None:
            object.__setattr__(
                self,
                "checkpoint_id",
                _require_text(self.checkpoint_id, "checkpoint_id"),
            )
        for field_name in (
            "manifest_count",
            "commit_receipt_count",
            "run_count",
            "current_count",
            "historically_valid_count",
            "missing_prefix_count",
            "conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count(getattr(self, field_name), field_name),
            )
        if not isinstance(self.assessments, tuple):
            raise TypeError("assessments must be a tuple")
        if not all(
            isinstance(value, DurableRunReceiptAssessment)
            for value in self.assessments
        ):
            raise TypeError(
                "assessments must contain DurableRunReceiptAssessment values"
            )
        if len(self.assessments) != self.run_count:
            raise ValueError("assessments must match run_count")
        run_ids = tuple(value.run_id for value in self.assessments)
        if len(set(run_ids)) != len(run_ids):
            raise ValueError("assessments must contain unique run identities")
        if not isinstance(self.rejected_run_ids, tuple):
            raise TypeError("rejected_run_ids must be a tuple")
        normalized_rejected = tuple(
            _require_text(value, "rejected_run_ids")
            for value in self.rejected_run_ids
        )
        object.__setattr__(
            self,
            "rejected_run_ids",
            normalized_rejected,
        )
        expected_rejected = tuple(
            value.run_id for value in self.assessments if not value.accepted
        )
        if self.rejected_run_ids != expected_rejected:
            raise ValueError(
                "rejected_run_ids must match rejected assessments"
            )
        status_total = (
            self.current_count
            + self.historically_valid_count
            + self.missing_prefix_count
            + self.conflict_count
        )
        if status_total != self.run_count:
            raise ValueError("status counts must equal run_count")
        actual_counts = {
            status: sum(value.status is status for value in self.assessments)
            for status in DurableRunReceiptStatus
        }
        if (
            self.current_count
            != actual_counts[DurableRunReceiptStatus.CURRENT]
            or self.historically_valid_count
            != actual_counts[DurableRunReceiptStatus.HISTORICALLY_VALID]
            or self.missing_prefix_count
            != actual_counts[DurableRunReceiptStatus.MISSING_PREFIX]
            or self.conflict_count
            != actual_counts[DurableRunReceiptStatus.CONFLICT]
        ):
            raise ValueError("status counts must match assessments")
        if self.schema_version != _MANIFEST_SCHEMA_VERSION:
            raise ValueError(
                "unsupported durable run receipt audit schema_version"
            )
        expected_id = deterministic_id(
            "durable_run_receipt_audit",
            self.identity_payload(),
        )
        if self.audit_id != expected_id:
            raise ValueError("audit_id does not match deterministic payload")

    @property
    def accepted_count(self) -> int:
        return self.current_count + self.historically_valid_count

    @property
    def rejected_count(self) -> int:
        return self.missing_prefix_count + self.conflict_count

    def identity_payload(self) -> dict[str, object]:
        return {
            "assessments": tuple(
                value.canonical_dict() for value in self.assessments
            ),
            "checkpoint_id": self.checkpoint_id,
            "commit_receipt_count": self.commit_receipt_count,
            "commit_receipt_store_hash": self.commit_receipt_store_hash,
            "conflict_count": self.conflict_count,
            "current_count": self.current_count,
            "historically_valid_count": self.historically_valid_count,
            "manifest_count": self.manifest_count,
            "manifest_store_hash": self.manifest_store_hash,
            "ledger_content_hash": self.ledger_content_hash,
            "missing_prefix_count": self.missing_prefix_count,
            "rejected_run_ids": self.rejected_run_ids,
            "run_count": self.run_count,
            "run_store_hash": self.run_store_hash,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, object]:
        return {"audit_id": self.audit_id, **self.identity_payload()}


class DurableRunReceiptAuditError(RuntimeError):
    def __init__(self, manifest: DurableRunReceiptAuditManifest) -> None:
        self.manifest = manifest
        super().__init__(
            "durable run receipt audit rejected runs: "
            f"{', '.join(manifest.rejected_run_ids)}"
        )


def _expected_verification_id(result: RecoveryGatedIngestionResult) -> str:
    decision = result.gate_decision
    payload: dict[str, object] = {
        "anchor_id": decision.trusted_anchor_id,
        "current_latest_audit_id": decision.latest_audit_id,
        "current_manifest_count": decision.manifest_count,
        "current_store_hash": decision.manifest_store_hash,
        "schema_version": _VERIFICATION_SCHEMA_VERSION,
        "status": TrustedAuditHeadStatus.CURRENT.value,
    }
    return deterministic_id("trusted_audit_head_verification", payload)


def _assess_result(
    *,
    result: RecoveryGatedIngestionResult,
    manifests: tuple[object, ...],
    manifest_store: PrefixVerifiableHistoricalAuditStore,
    receipts_by_session: dict[str, DurableIngestionCommitReceipt],
    ledger: HistoricalContentHashedEvidenceLedger,
    checkpoint_store: MarketStateCheckpointStore,
    current_store_hash: str,
    current_manifest_count: int,
) -> DurableRunReceiptAssessment:
    decision = result.gate_decision
    prefix_found = manifest_store.contains_content_hash(
        decision.manifest_store_hash,
        decision.manifest_count,
    )
    referenced_latest = (
        None
        if decision.manifest_count == 0
        or decision.manifest_count > len(manifests)
        else manifests[decision.manifest_count - 1].audit_id
    )
    commit_receipt = receipts_by_session.get(result.ingestion_session_id)
    commit_assessment = None
    commit_link_valid = result.ingestion_result.accepted_count == 0
    if commit_receipt is not None:
        commit_assessment = assess_historical_commit_receipt(
            receipt=commit_receipt,
            ledger=ledger,
            checkpoint_store=checkpoint_store,
        )
        commit_link_valid = (
            commit_receipt.accepted_count
            == result.ingestion_result.accepted_count
            and commit_receipt.provider_id
            == result.ingestion_result.provider_id
            and commit_receipt.market_id == result.ingestion_result.market_id
            and commit_receipt.checkpoint_id
            == result.ingestion_result.final_checkpoint_id
            and commit_assessment.status in _ACCEPTED_COMMIT_STATUSES
        )
    elif result.ingestion_result.accepted_count:
        commit_link_valid = False

    if not prefix_found:
        status = DurableRunReceiptStatus.MISSING_PREFIX
    elif (
        referenced_latest != decision.latest_audit_id
        or decision.verification_id != _expected_verification_id(result)
        or not commit_link_valid
    ):
        status = DurableRunReceiptStatus.CONFLICT
    elif (
        decision.manifest_count == current_manifest_count
        and hmac.compare_digest(
            decision.manifest_store_hash,
            current_store_hash,
        )
    ):
        status = DurableRunReceiptStatus.CURRENT
    else:
        status = DurableRunReceiptStatus.HISTORICALLY_VALID

    payload: dict[str, object] = {
        "gate_decision_id": result.gate_decision_id,
        "ingestion_session_id": result.ingestion_session_id,
        "commit_assessment_id": (
            None
            if commit_assessment is None
            else commit_assessment.assessment_id
        ),
        "commit_receipt_id": (
            None if commit_receipt is None else commit_receipt.receipt_id
        ),
        "commit_status": (
            None
            if commit_assessment is None
            else commit_assessment.status.value
        ),
        "referenced_latest_audit_id": decision.latest_audit_id,
        "referenced_manifest_count": decision.manifest_count,
        "referenced_manifest_hash": decision.manifest_store_hash,
        "run_id": result.run_id,
        "schema_version": _ASSESSMENT_SCHEMA_VERSION,
        "status": status.value,
        "trusted_anchor_id": decision.trusted_anchor_id,
        "verification_id": decision.verification_id,
    }
    return DurableRunReceiptAssessment(
        assessment_id=deterministic_id(
            "durable_run_receipt_assessment",
            payload,
        ),
        run_id=result.run_id,
        gate_decision_id=result.gate_decision_id,
        ingestion_session_id=result.ingestion_session_id,
        trusted_anchor_id=decision.trusted_anchor_id,
        verification_id=decision.verification_id,
        referenced_manifest_hash=decision.manifest_store_hash,
        referenced_manifest_count=decision.manifest_count,
        referenced_latest_audit_id=decision.latest_audit_id,
        commit_receipt_id=(
            None if commit_receipt is None else commit_receipt.receipt_id
        ),
        commit_assessment_id=(
            None
            if commit_assessment is None
            else commit_assessment.assessment_id
        ),
        commit_status=(
            None if commit_assessment is None else commit_assessment.status
        ),
        status=status,
    )


def audit_durable_run_receipts(
    *,
    run_store: RecoveryGatedRunStore,
    manifest_store: PrefixVerifiableHistoricalAuditStore,
    receipt_store: CommitReceiptStore,
    ledger: HistoricalContentHashedEvidenceLedger,
    checkpoint_store: MarketStateCheckpointStore,
) -> DurableRunReceiptAuditManifest:
    if not isinstance(run_store, RecoveryGatedRunStore):
        raise TypeError("run_store must satisfy RecoveryGatedRunStore")
    if not isinstance(manifest_store, PrefixVerifiableHistoricalAuditStore):
        raise TypeError("manifest_store must support prefix verification")
    if not isinstance(receipt_store, CommitReceiptStore):
        raise TypeError("receipt_store must satisfy CommitReceiptStore")
    if not isinstance(ledger, HistoricalContentHashedEvidenceLedger):
        raise TypeError("ledger must support historical content hashes")
    if not isinstance(checkpoint_store, MarketStateCheckpointStore):
        raise TypeError("checkpoint_store must satisfy its application port")

    run_snapshot = take_stable_collection_snapshot(
        name="run store",
        get_content_hash=lambda: run_store.content_hash,
        get_count=lambda: run_store.result_count,
        iterate=run_store.iter_results,
        identity=lambda result: result.run_id,
        lookup=run_store.get,
        item_type=RecoveryGatedIngestionResult,
    )
    run_store_hash, run_count, results = (
        run_snapshot.content_hash,
        run_snapshot.count,
        run_snapshot.items,
    )
    manifest_snapshot = take_stable_collection_snapshot(
        name="manifest store",
        get_content_hash=lambda: manifest_store.content_hash,
        get_count=lambda: manifest_store.manifest_count,
        iterate=manifest_store.iter_manifests,
        identity=lambda manifest: manifest.audit_id,
        lookup=manifest_store.get,
    )
    manifest_store_hash, manifest_count, manifests = (
        manifest_snapshot.content_hash,
        manifest_snapshot.count,
        manifest_snapshot.items,
    )
    receipt_snapshot = take_stable_collection_snapshot(
        name="receipt store",
        get_content_hash=lambda: receipt_store.content_hash,
        get_count=lambda: receipt_store.receipt_count,
        iterate=receipt_store.iter_receipts,
        identity=lambda receipt: receipt.receipt_id,
        lookup=receipt_store.get,
        item_type=DurableIngestionCommitReceipt,
    )
    receipt_store_hash, receipt_count, receipts = (
        receipt_snapshot.content_hash,
        receipt_snapshot.count,
        receipt_snapshot.items,
    )
    if len({receipt.session_id for receipt in receipts}) != receipt_count:
        raise RuntimeError(
            "receipt store contains multiple receipts for one session"
        )
    receipts_by_session = {
        receipt.session_id: receipt for receipt in receipts
    }

    ledger_content_hash = _require_sha256(
        ledger.content_hash,
        "ledger.content_hash",
    )
    try:
        checkpoint = checkpoint_store.load()
    except FileNotFoundError:
        checkpoint = None
    checkpoint_id = (
        None if checkpoint is None else checkpoint.checkpoint_id
    )

    assessments = tuple(
        _assess_result(
            result=result,
            manifests=manifests,
            manifest_store=manifest_store,
            receipts_by_session=receipts_by_session,
            ledger=ledger,
            checkpoint_store=checkpoint_store,
            current_store_hash=manifest_store_hash,
            current_manifest_count=manifest_count,
        )
        for result in results
    )
    assert_stable_collection_snapshot(
        run_snapshot,
        name="run store",
        get_content_hash=lambda: run_store.content_hash,
        get_count=lambda: run_store.result_count,
    )
    assert_stable_collection_snapshot(
        manifest_snapshot,
        name="manifest store",
        get_content_hash=lambda: manifest_store.content_hash,
        get_count=lambda: manifest_store.manifest_count,
    )
    assert_stable_collection_snapshot(
        receipt_snapshot,
        name="receipt store",
        get_content_hash=lambda: receipt_store.content_hash,
        get_count=lambda: receipt_store.receipt_count,
    )
    if not hmac.compare_digest(ledger.content_hash, ledger_content_hash):
        raise RuntimeError("Ledger changed during audit sweep")
    try:
        final_checkpoint = checkpoint_store.load()
    except FileNotFoundError:
        final_checkpoint = None
    final_checkpoint_id = (
        None if final_checkpoint is None else final_checkpoint.checkpoint_id
    )
    if final_checkpoint_id != checkpoint_id:
        raise RuntimeError("checkpoint changed during audit sweep")

    counts = {
        status: sum(value.status is status for value in assessments)
        for status in DurableRunReceiptStatus
    }
    rejected_run_ids = tuple(
        value.run_id for value in assessments if not value.accepted
    )
    payload: dict[str, object] = {
        "assessments": tuple(
            value.canonical_dict() for value in assessments
        ),
        "checkpoint_id": checkpoint_id,
        "commit_receipt_count": receipt_count,
        "commit_receipt_store_hash": receipt_store_hash,
        "conflict_count": counts[DurableRunReceiptStatus.CONFLICT],
        "current_count": counts[DurableRunReceiptStatus.CURRENT],
        "historically_valid_count": counts[
            DurableRunReceiptStatus.HISTORICALLY_VALID
        ],
        "manifest_count": manifest_count,
        "manifest_store_hash": manifest_store_hash,
        "ledger_content_hash": ledger_content_hash,
        "missing_prefix_count": counts[
            DurableRunReceiptStatus.MISSING_PREFIX
        ],
        "rejected_run_ids": rejected_run_ids,
        "run_count": run_count,
        "run_store_hash": run_store_hash,
        "schema_version": _MANIFEST_SCHEMA_VERSION,
    }
    return DurableRunReceiptAuditManifest(
        audit_id=deterministic_id("durable_run_receipt_audit", payload),
        run_store_hash=run_store_hash,
        manifest_store_hash=manifest_store_hash,
        commit_receipt_store_hash=receipt_store_hash,
        ledger_content_hash=ledger_content_hash,
        checkpoint_id=checkpoint_id,
        manifest_count=manifest_count,
        commit_receipt_count=receipt_count,
        run_count=run_count,
        current_count=counts[DurableRunReceiptStatus.CURRENT],
        historically_valid_count=counts[
            DurableRunReceiptStatus.HISTORICALLY_VALID
        ],
        missing_prefix_count=counts[
            DurableRunReceiptStatus.MISSING_PREFIX
        ],
        conflict_count=counts[DurableRunReceiptStatus.CONFLICT],
        assessments=assessments,
        rejected_run_ids=rejected_run_ids,
    )


def audit_durable_run_receipts_or_raise(
    *,
    run_store: RecoveryGatedRunStore,
    manifest_store: PrefixVerifiableHistoricalAuditStore,
    receipt_store: CommitReceiptStore,
    ledger: HistoricalContentHashedEvidenceLedger,
    checkpoint_store: MarketStateCheckpointStore,
) -> DurableRunReceiptAuditManifest:
    manifest = audit_durable_run_receipts(
        run_store=run_store,
        manifest_store=manifest_store,
        receipt_store=receipt_store,
        ledger=ledger,
        checkpoint_store=checkpoint_store,
    )
    if manifest.rejected_count:
        raise DurableRunReceiptAuditError(manifest)
    return manifest


__all__ = [
    "DurableRunReceiptAssessment",
    "DurableRunReceiptAuditError",
    "DurableRunReceiptAuditManifest",
    "DurableRunReceiptStatus",
    "audit_durable_run_receipts",
    "audit_durable_run_receipts_or_raise",
]
