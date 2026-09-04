from smart_money.adapters.persistence.early_entry_consistency_replay_store import JsonEarlyEntryConsistencyReplayStore
from smart_money.application.early_entry_consistency_replay_verifier import EarlyEntryConsistencyReplayReceipt
from smart_money.core.ids import deterministic_id


def test_early_entry_replay_store_is_atomic_canonical_and_idempotent(tmp_path) -> None:
    identity = {"consistency_id": "c-1", "matches": True, "schema_version": "early_entry_consistency_replay_verifier.v1"}
    receipt = EarlyEntryConsistencyReplayReceipt(
        **identity, replay_id=deterministic_id("early_entry_consistency_replay_verifier", identity)
    )
    store = JsonEarlyEntryConsistencyReplayStore(tmp_path / "replay.json")
    assert store.append(receipt) == receipt.replay_id
    assert store.append(receipt) == receipt.replay_id
    restored = JsonEarlyEntryConsistencyReplayStore(tmp_path / "replay.json")
    assert restored.get(receipt.replay_id) == receipt
    assert restored.receipt_count == 1
