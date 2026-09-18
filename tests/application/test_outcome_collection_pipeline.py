import pytest

from smart_money.application.outcome_collection_pipeline import (
    HumanCalibrationStatus,
    calibrate_dataset,
    materialize_outcome_dataset,
    review_calibration,
    run_due_outcome_job,
    schedule_outcomes,
)
from smart_money.application.point_in_time_outcome import (
    build_point_in_time_price_evidence,
)


def _price(at: int, quote: int):
    return build_point_in_time_price_evidence(mint="M", quote_mint="USDC", observed_at=at, slot=at, asset_amount_raw=100, quote_value_raw=quote, source_id="fixture")


def test_24h_72h_schedule_dataset_calibration_and_human_gate() -> None:
    start = _price(100, 1000)
    jobs = schedule_outcomes("candidate", start)
    assert [job.horizon_hours for job in jobs] == [24, 72]
    end = _price(jobs[0].due_at, 1500)
    outcome = run_due_outcome_job(jobs[0], start, end, as_of=jobs[0].due_at)
    dataset = materialize_outcome_dataset((outcome,), split="calibration")
    result = calibrate_dataset(dataset, predicted_scores_bps={"candidate": 8000}, success_return_bps=1000, failure_return_bps=-1000, max_calibration_error_bps=2500)
    review = review_calibration(result, reviewer="operator", approve=True, rationale="independent outcome passed")
    assert review.status is HumanCalibrationStatus.APPROVED


def test_evaluation_split_cannot_be_used_for_fitting() -> None:
    start = _price(100, 1000)
    job = schedule_outcomes("candidate", start)[0]
    outcome = run_due_outcome_job(job, start, _price(job.due_at, 1500), as_of=job.due_at)
    dataset = materialize_outcome_dataset((outcome,), split="evaluation")
    with pytest.raises(ValueError, match="cannot fit"):
        calibrate_dataset(dataset, predicted_scores_bps={"candidate": 8000}, success_return_bps=1000, failure_return_bps=-1000, max_calibration_error_bps=2500)
