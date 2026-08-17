from __future__ import annotations

import hmac
import re
from dataclasses import dataclass
from enum import Enum

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


def _require_count(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


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

    run_store_hash = _require_sha256(
        run_store.content_hash,
        "run_store.content_hash",
    )
    run_count = _require_count(run_store.result_count, "run_store.result_count")
    results = tuple(run_store.iter_results())
    if len(results) != run_count:
        raise RuntimeError("run store count changed before audit snapshot")
    if not all(
        isinstance(result, RecoveryGatedIngestionResult) for result in results
    ):
        raise RuntimeError("run store contains an invalid result type")
    if len({result.run_id for result in results}) != run_count:
        raise RuntimeError("run store snapshot contains duplicate identities")
    for result in results:
        if run_store.get(result.run_id) != result:
            raise RuntimeError("run store lookup disagrees with iteration")

    manifest_store_hash = _require_sha256(
        manifest_store.content_hash,
        "manifest_store.content_hash",
    )
    manifest_count = _require_count(
        manifest_store.manifest_count,
        "manifest_store.manifest_count",
    )
    manifests = tuple(manifest_store.iter_manifests())
    if len(manifests) != manifest_count:
        raise RuntimeError("manifest store count changed before audit snapshot")
    if len({manifest.audit_id for manifest in manifests}) != manifest_count:
        raise RuntimeError(
            "manifest store snapshot contains duplicate identities"
        )
    for manifest in manifests:
        if manifest_store.get(manifest.audit_id) != manifest:
            raise RuntimeError(
                "manifest store lookup disagrees with iteration"
            )

    receipt_store_hash = _require_sha256(
        receipt_store.content_hash,
        "receipt_store.content_hash",
    )
    receipt_count = _require_count(
        receipt_store.receipt_count,
        "receipt_store.receipt_count",
    )
    receipts = tuple(receipt_store.iter_receipts())
    if len(receipts) != receipt_count:
        raise RuntimeError("receipt store count changed before audit snapshot")
    if len({receipt.receipt_id for receipt in receipts}) != receipt_count:
        raise RuntimeError(
            "receipt store snapshot contains duplicate identities"
        )
    if len({receipt.session_id for receipt in receipts}) != receipt_count:
        raise RuntimeError(
            "receipt store contains multiple receipts for one session"
        )
    for receipt in receipts:
        if receipt_store.get(receipt.receipt_id) != receipt:
            raise RuntimeError(
                "receipt store lookup disagrees with iteration"
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
    if run_store.result_count != run_count or not hmac.compare_digest(
        run_store.content_hash,
        run_store_hash,
    ):
        raise RuntimeError("run store changed during audit sweep")
    if (
        manifest_store.manifest_count != manifest_count
        or not hmac.compare_digest(
            manifest_store.content_hash,
            manifest_store_hash,
        )
    ):
        raise RuntimeError("manifest store changed during audit sweep")
    if (
        receipt_store.receipt_count != receipt_count
        or not hmac.compare_digest(
            receipt_store.content_hash,
            receipt_store_hash,
        )
    ):
        raise RuntimeError("receipt store changed during audit sweep")
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
