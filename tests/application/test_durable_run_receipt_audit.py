from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from smart_money.adapters.persistence.commit_receipt_store import (
    JsonCommitReceiptStore,
)
from smart_money.adapters.persistence.durable_json_ledger import (
    DurableJsonEvidenceLedger,
)
from smart_money.adapters.persistence.historical_audit_manifest_store import (
    JsonHistoricalAuditManifestStore,
    JsonTrustedAuditHeadStore,
)
from smart_money.adapters.persistence.market_state_checkpoint_store import (
    JsonMarketStateCheckpointStore,
)
from smart_money.adapters.persistence.recovery_gated_run_store import (
    JsonRecoveryGatedRunStore,
)
from smart_money.application.audit_recovery_gate import (
    AuditRecoveryGateDecision,
    FailClosedAuditRecoveryGate,
)
from smart_money.application.checkpointed_ingestion import (
    CheckpointedIngestionResult,
)
from smart_money.application.durable_run_receipt_audit import (
    DurableRunReceiptAssessment,
    DurableRunReceiptAuditError,
    DurableRunReceiptAuditManifest,
    DurableRunReceiptStatus,
    audit_durable_run_receipts,
    audit_durable_run_receipts_or_raise,
)
from smart_money.application.historical_receipt_audit import (
    HistoricalReceiptAuditManifest,
)
from smart_money.application.recovery_gated_ingestion import (
    RecoveryGatedIngestionResult,
)
from smart_money.core.ids import deterministic_id


def _historical_manifest(marker: str) -> HistoricalReceiptAuditManifest:
    payload: dict[str, object] = {
        "assessment_ids": (f"assessment-{marker}",),
        "conflict_count": 0,
        "corrupted_count": 0,
        "current_count": 1,
        "drifted_count": 0,
        "historically_valid_count": 0,
        "ledger_content_hash": marker * 64,
        "missing_count": 0,
        "receipt_count": 1,
        "receipt_store_hash": marker * 64,
        "rejected_receipt_ids": (),
        "schema_version": "historical_receipt_audit.v1",
    }
    return HistoricalReceiptAuditManifest(
        audit_id=deterministic_id("historical_receipt_audit", payload),
        receipt_store_hash=marker * 64,
        ledger_content_hash=marker * 64,
        receipt_count=1,
        current_count=1,
        historically_valid_count=0,
        drifted_count=0,
        missing_count=0,
        corrupted_count=0,
        conflict_count=0,
        assessment_ids=(f"assessment-{marker}",),
        rejected_receipt_ids=(),
    )


def _result(
    decision: AuditRecoveryGateDecision,
    marker: str,
) -> RecoveryGatedIngestionResult:
    ingestion_payload: dict[str, object] = {
        "accepted_count": 0,
        "final_checkpoint_id": None,
        "first_accepted_event_id": None,
        "last_accepted_event_id": None,
        "market_id": f"market-{marker}",
        "provider_id": "evm.shadow.v3",
        "resumed_from_checkpoint_id": None,
        "schema_version": "checkpointed_ingestion_result.v1",
    }
    ingestion = CheckpointedIngestionResult(
        session_id=deterministic_id(
            "checkpointed_ingestion_result",
            ingestion_payload,
        ),
        provider_id="evm.shadow.v3",
        market_id=f"market-{marker}",
        resumed_from_checkpoint_id=None,
        first_accepted_event_id=None,
        last_accepted_event_id=None,
        accepted_count=0,
        final_checkpoint_id=None,
    )
    payload: dict[str, object] = {
        "gate_decision": decision.canonical_dict(),
        "ingestion_result": ingestion.canonical_dict(),
        "requested_max_events": 1,
        "schema_version": "recovery_gated_ingestion.v1",
    }
    return RecoveryGatedIngestionResult(
        run_id=deterministic_id("recovery_gated_ingestion", payload),
        gate_decision=decision,
        ingestion_result=ingestion,
        requested_max_events=1,
    )


def _accepted_result(
    decision: AuditRecoveryGateDecision,
    marker: str,
) -> RecoveryGatedIngestionResult:
    ingestion_payload: dict[str, object] = {
        "accepted_count": 1,
        "final_checkpoint_id": f"checkpoint-{marker}",
        "first_accepted_event_id": f"event-{marker}",
        "last_accepted_event_id": f"event-{marker}",
        "market_id": f"market-{marker}",
        "provider_id": "evm.shadow.v3",
        "resumed_from_checkpoint_id": None,
        "schema_version": "checkpointed_ingestion_result.v1",
    }
    ingestion = CheckpointedIngestionResult(
        session_id=deterministic_id(
            "checkpointed_ingestion_result",
            ingestion_payload,
        ),
        provider_id="evm.shadow.v3",
        market_id=f"market-{marker}",
        resumed_from_checkpoint_id=None,
        first_accepted_event_id=f"event-{marker}",
        last_accepted_event_id=f"event-{marker}",
        accepted_count=1,
        final_checkpoint_id=f"checkpoint-{marker}",
    )
    payload: dict[str, object] = {
        "gate_decision": decision.canonical_dict(),
        "ingestion_result": ingestion.canonical_dict(),
        "requested_max_events": 1,
        "schema_version": "recovery_gated_ingestion.v1",
    }
    return RecoveryGatedIngestionResult(
        run_id=deterministic_id("recovery_gated_ingestion", payload),
        gate_decision=decision,
        ingestion_result=ingestion,
        requested_max_events=1,
    )


def _gate(tmp_path):
    manifests = JsonHistoricalAuditManifestStore(
        tmp_path / "historical-audits.json"
    )
    heads = JsonTrustedAuditHeadStore(tmp_path / "trusted-head.json")
    return manifests, FailClosedAuditRecoveryGate(manifests, heads)


def _audit_dependencies(tmp_path):
    return {
        "receipt_store": JsonCommitReceiptStore(tmp_path / "receipts.json"),
        "ledger": DurableJsonEvidenceLedger(tmp_path / "ledger.json"),
        "checkpoint_store": JsonMarketStateCheckpointStore(
            tmp_path / "checkpoint.json"
        ),
    }


def test_manifest_distinguishes_current_and_historical_runs(tmp_path) -> None:
    manifests, gate = _gate(tmp_path)
    runs = JsonRecoveryGatedRunStore(tmp_path / "runs.json")
    manifests.append(_historical_manifest("a"))
    first = _result(
        gate.open_or_raise(advance_if_required=True),
        "a",
    )
    runs.append(first)
    manifests.append(_historical_manifest("b"))
    second = _result(
        gate.open_or_raise(advance_if_required=True),
        "b",
    )
    runs.append(second)

    manifest = audit_durable_run_receipts_or_raise(
        run_store=runs,
        manifest_store=manifests,
        **_audit_dependencies(tmp_path / "commit-state"),
    )
    repeated = audit_durable_run_receipts(
        run_store=runs,
        manifest_store=manifests,
        **_audit_dependencies(tmp_path / "commit-state"),
    )

    assert manifest == repeated
    assert manifest.run_count == 2
    assert manifest.current_count == 1
    assert manifest.historically_valid_count == 1
    assert manifest.accepted_count == 2
    assert manifest.rejected_count == 0
    assert tuple(value.run_id for value in manifest.assessments) == (
        first.run_id,
        second.run_id,
    )
    assert tuple(value.status for value in manifest.assessments) == (
        DurableRunReceiptStatus.HISTORICALLY_VALID,
        DurableRunReceiptStatus.CURRENT,
    )
    assert manifest.assessments[0].trusted_anchor_id == (
        first.gate_decision.trusted_anchor_id
    )
    assert not hasattr(manifest, "__dict__")
    with pytest.raises(FrozenInstanceError):
        manifest.run_count = 0  # type: ignore[misc]


def test_missing_prefix_is_rejected_by_strict_audit(tmp_path) -> None:
    source_manifests, source_gate = _gate(tmp_path / "source")
    source_manifests.append(_historical_manifest("a"))
    result = _result(
        source_gate.open_or_raise(advance_if_required=True),
        "a",
    )
    runs = JsonRecoveryGatedRunStore(tmp_path / "runs.json")
    runs.append(result)
    target_manifests = JsonHistoricalAuditManifestStore(
        tmp_path / "target.json"
    )

    manifest = audit_durable_run_receipts(
        run_store=runs,
        manifest_store=target_manifests,
        **_audit_dependencies(tmp_path / "commit-state"),
    )

    assert manifest.missing_prefix_count == 1
    assert manifest.rejected_run_ids == (result.run_id,)
    with pytest.raises(DurableRunReceiptAuditError) as caught:
        audit_durable_run_receipts_or_raise(
            run_store=runs,
            manifest_store=target_manifests,
            **_audit_dependencies(tmp_path / "commit-state"),
        )
    assert caught.value.manifest == manifest


def test_verification_linkage_conflict_is_detected(tmp_path) -> None:
    manifests, gate = _gate(tmp_path)
    manifests.append(_historical_manifest("a"))
    decision = gate.open_or_raise(advance_if_required=True)
    forged_payload = {
        **decision.identity_payload(),
        "verification_id": "forged-verification",
    }
    forged = AuditRecoveryGateDecision(
        decision_id=deterministic_id("audit_recovery_gate", forged_payload),
        status=decision.status,
        allowed=decision.allowed,
        advance_requested=decision.advance_requested,
        trusted_anchor_id=decision.trusted_anchor_id,
        verification_id="forged-verification",
        manifest_store_hash=decision.manifest_store_hash,
        manifest_count=decision.manifest_count,
        latest_audit_id=decision.latest_audit_id,
    )
    result = _result(forged, "a")
    runs = JsonRecoveryGatedRunStore(tmp_path / "runs.json")
    runs.append(result)

    manifest = audit_durable_run_receipts(
        run_store=runs,
        manifest_store=manifests,
        **_audit_dependencies(tmp_path / "commit-state"),
    )

    assert manifest.conflict_count == 1
    assert manifest.assessments[0].status is (
        DurableRunReceiptStatus.CONFLICT
    )


def test_empty_run_store_produces_empty_accepted_manifest(tmp_path) -> None:
    manifest = audit_durable_run_receipts_or_raise(
        run_store=JsonRecoveryGatedRunStore(tmp_path / "runs.json"),
        manifest_store=JsonHistoricalAuditManifestStore(
            tmp_path / "manifests.json"
        ),
        **_audit_dependencies(tmp_path / "commit-state"),
    )

    assert manifest.run_count == 0
    assert manifest.accepted_count == 0
    assert manifest.rejected_count == 0
    assert manifest.assessments == ()


def test_non_empty_run_requires_matching_durable_commit_receipt(
    tmp_path,
) -> None:
    manifests, gate = _gate(tmp_path)
    manifests.append(_historical_manifest("a"))
    result = _accepted_result(
        gate.open_or_raise(advance_if_required=True),
        "a",
    )
    runs = JsonRecoveryGatedRunStore(tmp_path / "runs.json")
    runs.append(result)

    manifest = audit_durable_run_receipts(
        run_store=runs,
        manifest_store=manifests,
        **_audit_dependencies(tmp_path / "commit-state"),
    )

    assert manifest.conflict_count == 1
    assert manifest.rejected_run_ids == (result.run_id,)
    assert manifest.assessments[0].commit_receipt_id is None


class _MissingLookupRunStore(JsonRecoveryGatedRunStore):
    def get(self, run_id: str) -> RecoveryGatedIngestionResult | None:
        return None


class _MutatingManifestStore(JsonHistoricalAuditManifestStore):
    def __init__(self, file_path, extra) -> None:
        super().__init__(file_path)
        self.extra = extra
        self.mutated = False

    def contains_content_hash(
        self,
        content_hash: str,
        manifest_count: int,
    ) -> bool:
        found = super().contains_content_hash(content_hash, manifest_count)
        if not self.mutated:
            self.mutated = True
            self.append(self.extra)
        return found


def test_store_inconsistency_and_concurrent_change_fail_closed(tmp_path) -> None:
    manifests, gate = _gate(tmp_path / "source")
    manifests.append(_historical_manifest("a"))
    result = _result(
        gate.open_or_raise(advance_if_required=True),
        "a",
    )
    inconsistent = _MissingLookupRunStore(tmp_path / "inconsistent.json")
    inconsistent.append(result)
    with pytest.raises(RuntimeError, match="lookup disagrees"):
        audit_durable_run_receipts(
            run_store=inconsistent,
            manifest_store=manifests,
            **_audit_dependencies(tmp_path / "inconsistent-state"),
        )

    changing = _MutatingManifestStore(
        tmp_path / "changing.json",
        _historical_manifest("b"),
    )
    changing.append(_historical_manifest("a"))
    stable_runs = JsonRecoveryGatedRunStore(tmp_path / "stable-runs.json")
    stable_runs.append(result)
    with pytest.raises(RuntimeError, match="manifest store changed"):
        audit_durable_run_receipts(
            run_store=stable_runs,
            manifest_store=changing,
            **_audit_dependencies(tmp_path / "changing-state"),
        )


def test_forged_assessment_and_manifest_identities_are_rejected(
    tmp_path,
) -> None:
    manifests, gate = _gate(tmp_path)
    manifests.append(_historical_manifest("a"))
    runs = JsonRecoveryGatedRunStore(tmp_path / "runs.json")
    runs.append(
        _result(gate.open_or_raise(advance_if_required=True), "a")
    )
    manifest = audit_durable_run_receipts(
        run_store=runs,
        manifest_store=manifests,
        **_audit_dependencies(tmp_path / "commit-state"),
    )
    assessment = manifest.assessments[0]

    with pytest.raises(ValueError, match="assessment_id"):
        DurableRunReceiptAssessment(
            **{
                **assessment.canonical_dict(),
                "assessment_id": "forged",
                "status": assessment.status,
            }
        )
    with pytest.raises(ValueError, match="audit_id"):
        DurableRunReceiptAuditManifest(
            **{
                **manifest.canonical_dict(),
                "audit_id": "forged",
                "assessments": manifest.assessments,
            }
        )
