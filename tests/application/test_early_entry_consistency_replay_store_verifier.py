from smart_money.adapters.persistence.early_entry_consistency_replay_store import JsonEarlyEntryConsistencyReplayStore
from smart_money.application.early_entry_consistency_replay_verifier import EarlyEntryConsistencyReplayReceipt
from smart_money.application.early_entry_consistency_replay_store_verifier import verify_early_entry_consistency_replay_store
from smart_money.core.ids import deterministic_id


def test_replay_store_verifier_matches_persisted_receipt(tmp_path) -> None:
    identity = {
        "consistency_id": "c-1",
        "matches": True,
        "schema_version": "early_entry_consistency_replay_verifier.v1",
    }
    expected = EarlyEntryConsistencyReplayReceipt(
        **identity,
        replay_id=deterministic_id("early_entry_consistency_replay_verifier", identity),
    )
    store = JsonEarlyEntryConsistencyReplayStore(tmp_path / "replay.json")
    store.append(expected)
    verification = verify_early_entry_consistency_replay_store(store, expected)
    assert verification.matches is True
    assert verification.replay_id == expected.replay_id
    assert verification.verification_id
