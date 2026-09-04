from smart_money.adapters.persistence.dashboard_query_replay_store import (
    JsonDashboardQueryReplayStore,
)
from smart_money.application.dashboard_query_replay_verifier import (
    DashboardQueryReplayReceipt,
)


def _receipt(matches: bool = True) -> DashboardQueryReplayReceipt:
    return DashboardQueryReplayReceipt(
        query_id="query-1",
        expected_receipt_id="expected-1",
        actual_receipt_id="actual-1",
        matches=matches,
        mismatches=() if matches else ("output_hash",),
    )


def test_replay_store_is_atomic_idempotent_and_reloadable(tmp_path) -> None:
    path = tmp_path / "replays.json"
    receipt = _receipt()
    store = JsonDashboardQueryReplayStore(path)

    assert store.append(receipt) == receipt.verification_id
    assert store.append(receipt) == receipt.verification_id
    reloaded = JsonDashboardQueryReplayStore(path)

    assert reloaded.get(receipt.verification_id) == receipt
    assert reloaded.receipt_count == 1
    assert reloaded.content_hash == store.content_hash


def test_replay_store_rejects_corruption(tmp_path) -> None:
    path = tmp_path / "replays.json"
    store = JsonDashboardQueryReplayStore(path)
    store.append(_receipt())
    path.write_text(path.read_text(encoding="utf-8") + "x", encoding="utf-8")

    try:
        JsonDashboardQueryReplayStore(path)
    except ValueError:
        pass
    else:
        raise AssertionError("corrupted replay store was accepted")
