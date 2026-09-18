import json

import pytest

from smart_money.adapters.persistence.dashboard_session_recovery_receipt_store import (
    JsonDashboardSessionRecoveryReceiptStore,
)
from smart_money.application.dashboard_session_recovery_gate import (
    DashboardSessionRecoveryReceipt,
)


def _receipt(decision: str = "READY") -> DashboardSessionRecoveryReceipt:
    return DashboardSessionRecoveryReceipt(
        decision=decision,
        reason_code=(
            "SESSION_CHAIN_HEAD_VERIFIED"
            if decision == "READY"
            else "MISSING_SESSION_CHAIN_OR_ANCHOR"
        ),
        anchor_id="anchor" if decision == "READY" else None,
        chain_id="chain" if decision == "READY" else None,
    )


def test_session_recovery_store_is_idempotent_and_reloadable(tmp_path) -> None:
    path = tmp_path / "session-recovery.json"
    receipt = _receipt()
    store = JsonDashboardSessionRecoveryReceiptStore(path)

    assert store.save(receipt) == receipt.receipt_id
    assert store.save(receipt) == receipt.receipt_id
    assert JsonDashboardSessionRecoveryReceiptStore(path).load() == receipt


def test_session_recovery_store_rejects_overwrite_and_corruption(tmp_path) -> None:
    path = tmp_path / "session-recovery.json"
    store = JsonDashboardSessionRecoveryReceiptStore(path)
    store.save(_receipt())
    with pytest.raises(RuntimeError, match="rollback"):
        store.save(_receipt("BLOCKED"))
    path.write_text(path.read_text(encoding="utf-8") + "x", encoding="utf-8")
    with pytest.raises(ValueError):
        JsonDashboardSessionRecoveryReceiptStore(path)


@pytest.mark.parametrize("mutation", ["missing_hash", "changed_payload"])
def test_session_recovery_valid_json_tamper_rejected(tmp_path, mutation):
    path = tmp_path / "receipt.json"
    JsonDashboardSessionRecoveryReceiptStore(path).save(_receipt())
    document = json.loads(path.read_text(encoding="utf-8"))
    if mutation == "missing_hash":
        del document["content_hash"]
    else:
        document["receipt"]["chain_id"] = "tampered"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError):
        JsonDashboardSessionRecoveryReceiptStore(path)
