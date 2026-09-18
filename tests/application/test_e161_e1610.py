from smart_money.application.historical_backfill import (
    TransactionBackfillStore, build_backfill_checkpoint, build_backfill_conflict,
    build_dataset_quality_report, build_historical_dataset, rebuild_historical_candidates,
    reconcile_historical_activity, schedule_historical_batches, verify_backfill_checkpoint,
    verify_backfill_release_gate, verify_backfill_replay,
)


def test_historical_backfill_pipeline(tmp_path) -> None:
    assert schedule_historical_batches(0, 5, 3) == ((0, 2), (3, 5))
    store = TransactionBackfillStore(tmp_path / "tx.json")
    store.save("sig", {"wallet": "w", "token": "t"})
    assert store.get("sig") == {"wallet": "w", "token": "t"}
    checkpoint = build_backfill_checkpoint(1, 5)
    assert verify_backfill_checkpoint(checkpoint, checkpoint)
    assert reconcile_historical_activity({"x": 1}, {"x": 1})
    assert build_backfill_conflict("t", ("rpc-a", "rpc-b"), "mismatch").evidence_id
    dataset = build_historical_dataset(({"wallet": "w", "token": "t"},))
    assert rebuild_historical_candidates(dataset)
    assert verify_backfill_replay(dataset, dataset)
    assert build_dataset_quality_report(dataset).quality_bps == 10000
    assert verify_backfill_release_gate(("decode",), ("decode",))
