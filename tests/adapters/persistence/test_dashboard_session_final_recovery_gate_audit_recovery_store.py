from __future__ import annotations

import json

import pytest

from smart_money.adapters.persistence import (
    dashboard_session_final_recovery_gate_audit_recovery_store as recovery_store,
)
from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_recovery_gate as recovery_gate,
)


def _receipt() -> recovery_gate.DashboardSessionFinalRecoveryGateAuditRecoveryReceipt:
    return recovery_gate.DashboardSessionFinalRecoveryGateAuditRecoveryReceipt(
        decision="READY",
        reason_code="GATE_AUDIT_CHAIN_RECOVERY_VERIFIED",
        chain_id="chain-1",
        replay_verification_id="replay-1",
    )


def test_append_is_idempotent_and_reloads(tmp_path) -> None:
    path = tmp_path / "recovery_audit_recovery.json"
    store = recovery_store.JsonDashboardSessionFinalRecoveryGateAuditRecoveryStore(path)
    receipt = _receipt()

    assert store.append(receipt) == receipt.receipt_id
    assert store.append(receipt) == receipt.receipt_id

    restored = recovery_store.JsonDashboardSessionFinalRecoveryGateAuditRecoveryStore(path)
    assert restored.receipt_count == 1
    assert restored.get(receipt.receipt_id) == receipt
    assert list(restored.iter_receipts()) == [receipt]


def test_hash_corruption_is_rejected(tmp_path) -> None:
    path = tmp_path / "recovery_audit_recovery.json"
    store = recovery_store.JsonDashboardSessionFinalRecoveryGateAuditRecoveryStore(path)
    store.append(_receipt())
    document = json.loads(path.read_text(encoding="utf-8"))
    document["content_hash"] = "f" * 64
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        recovery_store.JsonDashboardSessionFinalRecoveryGateAuditRecoveryStore(path)
