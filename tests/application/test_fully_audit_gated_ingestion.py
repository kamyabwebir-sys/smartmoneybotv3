from pathlib import Path

import pytest

from smart_money.adapters.persistence.durable_run_receipt_audit_manifest_store import (
    JsonDurableRunReceiptAuditManifestStore,
    JsonTrustedDurableRunAuditHeadStore,
)
from smart_money.application.durable_run_audit_recovery_gate import (
    FailClosedDurableRunAuditRecoveryGate,
)
from smart_money.application.fully_audit_gated_ingestion import (
    FullyAuditGatedIngestionOrchestrator,
)
from tests.adapters.persistence.test_durable_run_receipt_audit_manifest_store import (
    _manifest,
)
from tests.application.test_durable_recovery_gated_ingestion import (
    _market,
    _result,
)


class _Ingestion:
    async def run(self, market, **kwargs):
        from smart_money.application.durable_recovery_gated_ingestion import (
            DurableRecoveryGatedIngestionReceipt,
        )
        from smart_money.core.ids import deterministic_id

        result = _result(market)
        payload = {
            "newly_persisted": True,
            "result": result.canonical_dict(),
            "run_store_content_hash": "0" * 64,
            "run_store_result_count": 1,
            "schema_version": "durable_recovery_gated_ingestion.v1",
        }
        return DurableRecoveryGatedIngestionReceipt(
            receipt_id=deterministic_id(
                "durable_recovery_gated_ingestion", payload
            ),
            result=result,
            run_store_content_hash="0" * 64,
            run_store_result_count=1,
            newly_persisted=True,
        )


class _Audit:
    def run(self):
        return _manifest()


@pytest.mark.asyncio
async def test_orchestrator_enforces_pre_gate_and_anchors_post_audit(
    tmp_path: Path,
) -> None:
    audits = JsonDurableRunReceiptAuditManifestStore(tmp_path / "audit.json")
    heads = JsonTrustedDurableRunAuditHeadStore(tmp_path / "head.json")
    gate = FailClosedDurableRunAuditRecoveryGate(audits, heads)
    orchestrator = FullyAuditGatedIngestionOrchestrator(
        gate,
        _Ingestion(),
        _Audit(),
        audits,
        heads,
    )
    result = await orchestrator.run(_market(), advance_if_required=True)
    assert audits.get(result.audit_manifest.audit_id) == result.audit_manifest
    assert heads.load() == result.trusted_head
    assert result.gate_decision.allowed
