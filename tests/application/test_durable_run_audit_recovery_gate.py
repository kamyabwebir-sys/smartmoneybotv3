from pathlib import Path

import pytest

from smart_money.adapters.persistence.durable_run_receipt_audit_manifest_store import (
    JsonDurableRunReceiptAuditManifestStore,
    JsonTrustedDurableRunAuditHeadStore,
)
from smart_money.application.durable_run_audit_recovery_gate import (
    DurableRunAuditRecoveryGateBlockedError,
    DurableRunAuditRecoveryGateStatus,
    FailClosedDurableRunAuditRecoveryGate,
)
from tests.adapters.persistence.test_durable_run_receipt_audit_manifest_store import (
    _manifest,
)


def test_gate_fails_closed_then_can_create_current_anchor(
    tmp_path: Path,
) -> None:
    manifests = JsonDurableRunReceiptAuditManifestStore(tmp_path / "audit.json")
    manifests.append(_manifest())
    gate = FailClosedDurableRunAuditRecoveryGate(
        manifests,
        JsonTrustedDurableRunAuditHeadStore(tmp_path / "head.json"),
    )
    with pytest.raises(DurableRunAuditRecoveryGateBlockedError):
        gate.open_or_raise()
    decision = gate.open_or_raise(advance_if_required=True)
    assert decision.allowed
    assert decision.status is DurableRunAuditRecoveryGateStatus.READY_ADVANCED
    assert (
        gate.open_or_raise().status
        is DurableRunAuditRecoveryGateStatus.READY_CURRENT
    )
