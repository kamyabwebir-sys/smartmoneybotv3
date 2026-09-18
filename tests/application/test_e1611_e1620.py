from smart_money.application.historical_execution import (
    BackfillProgressStore, audit_historical_dataset, bind_historical_decoder,
    execute_backfill_batch, extract_historical_token_activity,
    extract_historical_wallet_activity, generate_historical_candidates,
    join_candidate_outcomes, retry_transaction_batch,
    verify_historical_production_gate,
)


def test_historical_execution_pipeline(tmp_path) -> None:
    tx = execute_backfill_batch(lambda a, b: ({"slot": a},), (1, 2))
    assert tx
    assert retry_transaction_batch(lambda: "ok", 1) == "ok"
    progress = BackfillProgressStore(tmp_path / "progress.json")
    progress.save(1, 2)
    assert progress.load() == (1, 2)
    decoded = bind_historical_decoder(
        lambda x: {"activities": [{"wallet": "w", "token": "t", "slot": 1}]}, tx[0]
    )
    activities = extract_historical_wallet_activity(decoded)
    assert extract_historical_token_activity(decoded)
    candidates = generate_historical_candidates(activities)
    joined = join_candidate_outcomes(
        candidates, {candidates[0]["candidate_id"]: {"success": True}}
    )
    assert joined[0]["outcome"]["success"]
    assert audit_historical_dataset(joined).candidate_count == 1
    assert verify_historical_production_gate(("decode",), ("decode",))
