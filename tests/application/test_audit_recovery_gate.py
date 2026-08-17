from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from smart_money.adapters.persistence.historical_audit_manifest_store import (
    JsonHistoricalAuditManifestStore,
    JsonTrustedAuditHeadStore,
)
from smart_money.application.audit_recovery_gate import (
    AuditRecoveryGateBlockedError,
    AuditRecoveryGateDecision,
    AuditRecoveryGateStatus,
    FailClosedAuditRecoveryGate,
)
from smart_money.application.historical_receipt_audit import (
    HistoricalReceiptAuditManifest,
)
from smart_money.application.trusted_audit_head import (
    advance_trusted_audit_head,
    make_trusted_audit_head,
)
from smart_money.core.ids import deterministic_id


def _manifest(marker: str) -> HistoricalReceiptAuditManifest:
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


def _gate(tmp_path):
    manifests = JsonHistoricalAuditManifestStore(
        tmp_path / "historical-audits.json"
    )
    heads = JsonTrustedAuditHeadStore(tmp_path / "trusted-head.json")
    return manifests, heads, FailClosedAuditRecoveryGate(manifests, heads)


@pytest.mark.asyncio
async def test_missing_head_blocks_operation_without_explicit_advance(
    tmp_path,
) -> None:
    manifests, heads, gate = _gate(tmp_path)
    manifests.append(_manifest("a"))
    calls: list[str] = []

    async def operation() -> str:
        calls.append("called")
        return "result"

    blocked = gate.evaluate()
    with pytest.raises(AuditRecoveryGateBlockedError) as caught:
        await gate.run_guarded(operation)

    assert blocked.status is AuditRecoveryGateStatus.BLOCKED_MISSING_HEAD
    assert blocked.allowed is False
    assert caught.value.decision == blocked
    assert calls == []
    assert not heads.file_path.exists()


@pytest.mark.asyncio
async def test_explicit_bootstrap_opens_gate_then_current_is_byte_stable(
    tmp_path,
) -> None:
    manifests, heads, gate = _gate(tmp_path)
    manifests.append(_manifest("a"))
    calls: list[str] = []

    async def operation() -> str:
        calls.append("called")
        return "accepted"

    advanced, result = await gate.run_guarded(
        operation,
        advance_if_required=True,
    )
    head_bytes = heads.file_path.read_bytes()
    current, repeated_result = await gate.run_guarded(operation)

    assert advanced.status is AuditRecoveryGateStatus.READY_ADVANCED
    assert advanced.advance_requested is True
    assert result == repeated_result == "accepted"
    assert current.status is AuditRecoveryGateStatus.READY_CURRENT
    assert current.advance_requested is False
    assert calls == ["called", "called"]
    assert heads.file_path.read_bytes() == head_bytes


@pytest.mark.asyncio
async def test_unanchored_advance_requires_explicit_request(tmp_path) -> None:
    manifests, heads, gate = _gate(tmp_path)
    manifests.append(_manifest("a"))
    first_head = advance_trusted_audit_head(
        manifest_store=manifests,
        head_store=heads,
    )
    manifests.append(_manifest("b"))
    calls: list[str] = []

    async def operation() -> int:
        calls.append("called")
        return 2

    blocked = gate.evaluate()
    with pytest.raises(AuditRecoveryGateBlockedError):
        await gate.run_guarded(operation)
    advanced, result = await gate.run_guarded(
        operation,
        advance_if_required=True,
    )

    assert blocked.status is AuditRecoveryGateStatus.BLOCKED_ADVANCE_REQUIRED
    assert calls == ["called"]
    assert result == 2
    assert advanced.status is AuditRecoveryGateStatus.READY_ADVANCED
    assert heads.load().previous_anchor_id == first_head.anchor_id


@pytest.mark.asyncio
async def test_rollback_and_divergence_block_even_explicit_advance(
    tmp_path,
) -> None:
    source = JsonHistoricalAuditManifestStore(tmp_path / "source.json")
    source.append(_manifest("a"))
    source.append(_manifest("b"))
    trusted_head = make_trusted_audit_head(manifest_store=source)

    rollback = JsonHistoricalAuditManifestStore(tmp_path / "rollback.json")
    rollback.append(_manifest("a"))
    rollback_heads = JsonTrustedAuditHeadStore(
        tmp_path / "rollback-head.json"
    )
    rollback_heads.save(trusted_head)

    divergent = JsonHistoricalAuditManifestStore(tmp_path / "divergent.json")
    divergent.append(_manifest("a"))
    divergent.append(_manifest("c"))
    divergent_heads = JsonTrustedAuditHeadStore(
        tmp_path / "divergent-head.json"
    )
    divergent_heads.save(trusted_head)
    calls: list[str] = []

    async def operation() -> None:
        calls.append("called")

    rollback_gate = FailClosedAuditRecoveryGate(
        rollback,
        rollback_heads,
    )
    divergent_gate = FailClosedAuditRecoveryGate(
        divergent,
        divergent_heads,
    )

    with pytest.raises(AuditRecoveryGateBlockedError) as rollback_error:
        await rollback_gate.run_guarded(
            operation,
            advance_if_required=True,
        )
    with pytest.raises(AuditRecoveryGateBlockedError) as divergent_error:
        await divergent_gate.run_guarded(
            operation,
            advance_if_required=True,
        )

    assert (
        rollback_error.value.decision.status
        is AuditRecoveryGateStatus.BLOCKED_ROLLBACK
    )
    assert (
        divergent_error.value.decision.status
        is AuditRecoveryGateStatus.BLOCKED_DIVERGED
    )
    assert calls == []


@pytest.mark.asyncio
async def test_corrupted_head_fails_before_operation(tmp_path) -> None:
    manifests, heads, gate = _gate(tmp_path)
    manifests.append(_manifest("a"))
    advance_trusted_audit_head(
        manifest_store=manifests,
        head_store=heads,
    )
    document = json.loads(heads.file_path.read_text(encoding="utf-8"))
    document["head"]["manifest_count"] = 0
    heads.file_path.write_text(json.dumps(document), encoding="utf-8")
    calls: list[str] = []

    async def operation() -> None:
        calls.append("called")

    with pytest.raises(ValueError, match="content hash mismatch"):
        await gate.run_guarded(operation)

    assert calls == []


def test_decision_is_deterministic_immutable_and_rejects_forgery(
    tmp_path,
) -> None:
    manifests, _, gate = _gate(tmp_path)
    manifests.append(_manifest("a"))

    first = gate.evaluate()
    second = gate.evaluate()

    assert first == second
    assert not hasattr(first, "__dict__")
    with pytest.raises(FrozenInstanceError):
        first.allowed = True  # type: ignore[misc]
    with pytest.raises(ValueError, match="decision_id"):
        AuditRecoveryGateDecision(
            **{
                **first.canonical_dict(),
                "decision_id": "forged",
                "status": first.status,
            }
        )
