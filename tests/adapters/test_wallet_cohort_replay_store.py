from smart_money.adapters.persistence.wallet_cohort_replay_store import JsonWalletCohortReplayStore
from smart_money.application.wallet_cohort_replay import WalletCohortReplayReceipt
from smart_money.core.ids import deterministic_id


def test_wallet_cohort_replay_store_is_idempotent_and_reloadable(tmp_path) -> None:
    identity = {"cohort_id": "cohort-1", "matches": True, "schema_version": "wallet_cohort_replay.v1"}
    receipt = WalletCohortReplayReceipt(
        **identity, replay_id=deterministic_id("wallet_cohort_replay", identity)
    )
    path = tmp_path / "cohort-replay.json"
    store = JsonWalletCohortReplayStore(path)
    assert store.append(receipt) == receipt.replay_id
    assert store.append(receipt) == receipt.replay_id
    restored = JsonWalletCohortReplayStore(path)
    assert restored.get(receipt.replay_id) == receipt
    assert restored.receipt_count == 1
