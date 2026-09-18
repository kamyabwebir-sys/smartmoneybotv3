import pytest

from smart_money.adapters.persistence.dashboard_recovery_replay_store import (
    JsonDashboardRecoveryReplayStore,
)
from smart_money.application.dashboard_recovery_replay_verifier import (
    DashboardRecoveryReplayReceipt,
)


def _receipt(matches: bool = True) -> DashboardRecoveryReplayReceipt:
    return DashboardRecoveryReplayReceipt(
        expected_receipt_id="expected",
        actual_receipt_id="actual",
        matches=matches,
        mismatches=() if matches else ("decision",),
    )


def test_recovery_replay_store_is_idempotent_and_reloadable(tmp_path) -> None:
    path = tmp_path / "recovery-replays.json"
    receipt = _receipt()
    store = JsonDashboardRecoveryReplayStore(path)

    assert store.append(receipt) == receipt.verification_id
    assert store.append(receipt) == receipt.verification_id
    reloaded = JsonDashboardRecoveryReplayStore(path)

    assert reloaded.get(receipt.verification_id) == receipt
    assert reloaded.receipt_count == 1
    assert reloaded.content_hash == store.content_hash


def test_recovery_replay_store_rejects_corruption(tmp_path) -> None:
    path = tmp_path / "recovery-replays.json"
    store = JsonDashboardRecoveryReplayStore(path)
    store.append(_receipt())
    path.write_text(path.read_text(encoding="utf-8") + "x", encoding="utf-8")

    with pytest.raises(ValueError):
        JsonDashboardRecoveryReplayStore(path)
