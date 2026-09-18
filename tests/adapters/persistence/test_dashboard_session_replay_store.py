import pytest

from smart_money.adapters.persistence.dashboard_session_replay_store import (
    JsonDashboardSessionReplayStore,
)
from smart_money.application.dashboard_recovery_session_replay_verifier import (
    DashboardSessionReplayReceipt,
)


def _receipt(matches: bool = True) -> DashboardSessionReplayReceipt:
    return DashboardSessionReplayReceipt(
        expected_session_id="expected",
        actual_session_id="actual",
        matches=matches,
        mismatches=() if matches else ("session_status",),
    )


def test_session_replay_store_is_idempotent_and_reloadable(tmp_path) -> None:
    path = tmp_path / "session-replays.json"
    receipt = _receipt()
    store = JsonDashboardSessionReplayStore(path)

    assert store.append(receipt) == receipt.verification_id
    assert store.append(receipt) == receipt.verification_id
    reloaded = JsonDashboardSessionReplayStore(path)

    assert reloaded.get(receipt.verification_id) == receipt
    assert reloaded.receipt_count == 1
    assert reloaded.content_hash == store.content_hash


def test_session_replay_store_rejects_corruption(tmp_path) -> None:
    path = tmp_path / "session-replays.json"
    store = JsonDashboardSessionReplayStore(path)
    store.append(_receipt())
    path.write_text(path.read_text(encoding="utf-8") + "x", encoding="utf-8")

    with pytest.raises(ValueError):
        JsonDashboardSessionReplayStore(path)
