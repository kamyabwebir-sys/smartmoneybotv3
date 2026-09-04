import pytest

from smart_money.adapters.persistence.dashboard_audit_recovery_receipt_store import (
    JsonDashboardAuditRecoveryReceiptStore,
)
from smart_money.application.dashboard_audit_recovery_gate import (
    DashboardAuditRecoveryReceipt,
)


def _receipt(decision: str = "READY") -> DashboardAuditRecoveryReceipt:
    return DashboardAuditRecoveryReceipt(
        decision=decision,
        reason_code="CHAIN_HEAD_VERIFIED" if decision == "READY" else "MISSING_CHAIN_OR_ANCHOR",
        anchor_id="anchor" if decision == "READY" else None,
        chain_id="chain" if decision == "READY" else None,
    )


def test_recovery_store_is_atomic_idempotent_and_reloadable(tmp_path) -> None:
    path = tmp_path / "recovery.json"
    receipt = _receipt()
    store = JsonDashboardAuditRecoveryReceiptStore(path)

    assert store.save(receipt) == receipt.receipt_id
    assert store.save(receipt) == receipt.receipt_id
    assert JsonDashboardAuditRecoveryReceiptStore(path).load() == receipt


def test_recovery_store_rejects_overwrite_and_corruption(tmp_path) -> None:
    path = tmp_path / "recovery.json"
    store = JsonDashboardAuditRecoveryReceiptStore(path)
    store.save(_receipt())
    with pytest.raises(RuntimeError, match="rollback"):
        store.save(_receipt("BLOCKED"))
    path.write_text(path.read_text(encoding="utf-8") + "x", encoding="utf-8")
    with pytest.raises(ValueError):
        JsonDashboardAuditRecoveryReceiptStore(path)
