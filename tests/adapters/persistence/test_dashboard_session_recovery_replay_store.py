import pytest

from smart_money.adapters.persistence.dashboard_session_recovery_replay_store import (
    JsonDashboardSessionRecoveryReplayStore,
)
from smart_money.application.dashboard_session_recovery_replay_verifier import (
    DashboardSessionRecoveryReplayReceipt,
)


def _receipt(matches: bool = True) -> DashboardSessionRecoveryReplayReceipt:
    return DashboardSessionRecoveryReplayReceipt(
        expected_receipt_id="expected",
        actual_receipt_id="actual",
        matches=matches,
        mismatches=() if matches else ("decision",),
    )


def test_store_is_idempotent_and_reloadable(tmp_path) -> None:
    path = tmp_path / "session-recovery-replays.json"
    receipt = _receipt()
    store = JsonDashboardSessionRecoveryReplayStore(path)

    assert store.append(receipt) == receipt.verification_id
    assert store.append(receipt) == receipt.verification_id
    reloaded = JsonDashboardSessionRecoveryReplayStore(path)

    assert reloaded.get(receipt.verification_id) == receipt
    assert reloaded.receipt_count == 1
    assert reloaded.content_hash == store.content_hash


def test_store_rejects_corruption(tmp_path) -> None:
    path = tmp_path / "session-recovery-replays.json"
    store = JsonDashboardSessionRecoveryReplayStore(path)
    store.append(_receipt())
    path.write_text(path.read_text(encoding="utf-8") + "x", encoding="utf-8")

    with pytest.raises(ValueError):
        JsonDashboardSessionRecoveryReplayStore(path)
