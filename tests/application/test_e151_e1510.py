from smart_money.application.candidate_validation import (
    audit_candidate_dashboard, bind_historical_outcome, build_candidate_replay_session,
    build_historical_backfill, calibrate_confidence, classify_false_positive,
    evaluate_precision_recall, verify_production_release_gate,
)


def test_candidate_validation_and_release_gate() -> None:
    assert bind_historical_outcome("c", "o").binding_id
    metrics = evaluate_precision_recall(8, 2, 2)
    assert metrics.precision_bps == 8000
    assert classify_false_positive(True, False) == "FALSE_POSITIVE"
    assert calibrate_confidence(8000, 6000).calibrated_score_bps == 7000
    assert build_historical_backfill(("w", "t"), 1, 10).backfill_id
    assert build_candidate_replay_session(("c",)).replay_id
    assert audit_candidate_dashboard("dashboard", 1).audit_id
    assert verify_production_release_gate(("replay", "metrics"), ("replay", "metrics"))
