import pytest

from smart_money.adapters.persistence.dashboard_recovery_session_store import (
    JsonDashboardRecoverySessionStore,
)
from smart_money.application.dashboard_recovery_query_session import (
    DashboardRecoveryQuerySessionReceipt,
)


def _receipt(status: str = "EXECUTED"):
    return DashboardRecoveryQuerySessionReceipt(
        session_status=status,
        recovery_receipt_id="recovery-1",
        query_id="query-1" if status == "EXECUTED" else None,
        query_receipt_id="receipt-1" if status == "EXECUTED" else None,
        reason_code=(
            "RECOVERY_GATE_READY"
            if status == "EXECUTED"
            else "RECOVERY_GATE_BLOCKED"
        ),
    )


def test_session_store_is_idempotent_and_reloadable(tmp_path) -> None:
    path = tmp_path / "sessions.json"
    receipt = _receipt()
    store = JsonDashboardRecoverySessionStore(path)

    assert store.append(receipt) == receipt.session_id
    assert store.append(receipt) == receipt.session_id
    reloaded = JsonDashboardRecoverySessionStore(path)

    assert reloaded.get(receipt.session_id) == receipt
    assert reloaded.receipt_count == 1
    assert reloaded.content_hash == store.content_hash


def test_session_store_rejects_corruption(tmp_path) -> None:
    path = tmp_path / "sessions.json"
    store = JsonDashboardRecoverySessionStore(path)
    store.append(_receipt())
    path.write_text(path.read_text(encoding="utf-8") + "x", encoding="utf-8")

    with pytest.raises(ValueError):
        JsonDashboardRecoverySessionStore(path)
