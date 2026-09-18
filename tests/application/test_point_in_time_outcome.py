import pytest

from smart_money.application.point_in_time_outcome import (
    OutcomeCollectionStatus,
    build_point_in_time_price_evidence,
    calibrate_completed_outcomes,
    collect_candidate_outcome,
    verify_candidate_outcome_replay,
)


def price(at: int, quote: int):
    return build_point_in_time_price_evidence(
        mint="M",
        quote_mint="USDC",
        observed_at=at,
        slot=at,
        asset_amount_raw=100,
        quote_value_raw=quote,
        source_id="fixture",
    )


def test_outcome_stays_pending_before_maturity() -> None:
    result = collect_candidate_outcome("c1", price(100, 1000), None, horizon_hours=24, as_of=200)
    assert result.status is OutcomeCollectionStatus.PENDING
    assert result.return_bps is None


def test_completed_outcome_is_integer_replayable_and_calibrated() -> None:
    start, end = price(100, 1000), price(100 + 24 * 3600, 1500)
    outcome = collect_candidate_outcome(
        "c1", start, end, horizon_hours=24, as_of=end.observed_at
    )

    assert outcome.status is OutcomeCollectionStatus.COMPLETE
    assert outcome.return_bps == 5000
    assert verify_candidate_outcome_replay(outcome, start, end, as_of=end.observed_at)
    result = calibrate_completed_outcomes(
        (outcome,),
        predicted_scores_bps={"c1": 8000},
        success_return_bps=1000,
        failure_return_bps=-1000,
        max_calibration_error_bps=2500,
    )
    assert result.precision_recall.precision_bps == 10000
    assert result.precision_recall.recall_bps == 10000
    assert result.governance_gate.passed


def test_rejects_premature_or_cross_asset_end_evidence() -> None:
    start = price(100, 1000)
    with pytest.raises(ValueError, match="precedes"):
        collect_candidate_outcome("c", start, price(200, 1000), horizon_hours=24, as_of=100 + 24 * 3600)
