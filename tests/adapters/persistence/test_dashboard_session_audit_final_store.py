from __future__ import annotations

import json

import pytest

from smart_money.adapters.persistence.dashboard_session_audit_final_store import (
    JsonDashboardSessionAuditFinalStore,
)
from smart_money.application.dashboard_session_audit_finalizer import (
    DashboardSessionAuditFinalReceipt,
)


def _receipt(reason: str = "SESSION_AUDIT_CHAIN_FINALIZED"):
    return DashboardSessionAuditFinalReceipt(
        chain_id="chain-1",
        chain_hash="0" * 64,
        head_anchor_id="anchor-1",
        recovery_receipt_id="recovery-1",
        recovery_replay_verification_id="replay-1",
        entry_count=0,
        decision="READY",
        reason_code=reason,
    )


def test_append_is_atomic_idempotent_and_reloads(tmp_path) -> None:
    path = tmp_path / "final.json"
    receipt = _receipt()
    store = JsonDashboardSessionAuditFinalStore(path)

    assert store.append(receipt) == receipt.receipt_id
    assert store.append(receipt) == receipt.receipt_id
    assert store.receipt_count == 1
    assert store.content_hash

    restored = JsonDashboardSessionAuditFinalStore(path)
    assert restored.get(receipt.receipt_id) == receipt
    assert list(restored.iter_receipts()) == [receipt]


def test_corruption_and_collision_fail_closed(tmp_path) -> None:
    path = tmp_path / "final.json"
    receipt = _receipt()
    store = JsonDashboardSessionAuditFinalStore(path)
    store.append(receipt)
    document = json.loads(path.read_text(encoding="utf-8"))
    document["content_hash"] = "f" * 64
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        JsonDashboardSessionAuditFinalStore(path)

    other = _receipt("OTHER_REASON")
    with pytest.raises(RuntimeError, match="identity collision"):
        store._receipts[other.receipt_id] = receipt
        store.append(other)
