from smart_money.application.candidate_quality import (
    CandidateLabel,
    FalsePositiveCause,
    build_confidence_calibration_report,
    analyze_wallet_cohort_performance,
    analyze_token_lifecycle_performance,
    evaluate_walk_forward_stability,
    build_candidate_quality_dashboard,
    evaluate_calibration_governance_gate,
    analyze_false_positive,
    analyze_precision_recall,
    build_candidate_quality_label,
    generate_outcome_label,
)
from smart_money.application.outcome_learning import extract_token_outcome


def test_candidate_quality_label_is_deterministic_and_normalized() -> None:
    left = build_candidate_quality_label(
        " candidate-1 ", " outcome-1 ", "24h", CandidateLabel.VALIDATED, " retained liquidity "
    )
    right = build_candidate_quality_label(
        "candidate-1", "outcome-1", "24h", CandidateLabel.VALIDATED, "retained liquidity"
    )
    assert left == right
    assert left.label_id.startswith("candidate-quality-label_")


def test_candidate_quality_label_rejects_invalid_input() -> None:
    try:
        build_candidate_quality_label("", "outcome", "1h", CandidateLabel.FAILED, "reason")
    except ValueError:
        pass
    else:
        raise AssertionError("empty candidate id must fail closed")


def test_outcome_label_generation_covers_all_label_states() -> None:
    cases = (
        (120, CandidateLabel.VALIDATED),
        (80, CandidateLabel.FAILED),
        (100, CandidateLabel.INCONCLUSIVE),
    )
    for end_value, expected in cases:
        observation = extract_token_outcome(
            "token-1",
            start_slot=10,
            end_slot=20,
            start_value=100,
            end_value=end_value,
        )
        label = generate_outcome_label(
            "candidate-1",
            observation,
            "10-slots",
            success_delta=10,
            failure_delta=-10,
        )
        assert label.label is expected
        assert label.outcome_id == observation.outcome_id


def test_outcome_label_generation_is_replay_stable_and_fail_closed() -> None:
    observation = extract_token_outcome(
        "token-1", start_slot=10, end_slot=20, start_value=100, end_value=112
    )
    first = generate_outcome_label("candidate-1", observation, "10-slots")
    replayed = generate_outcome_label("candidate-1", observation, "10-slots")
    assert first == replayed

    try:
        generate_outcome_label(
            "candidate-1",
            observation,
            "10-slots",
            success_delta=0,
            failure_delta=0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("overlapping thresholds must fail closed")


def test_precision_recall_window_is_deterministic_and_excludes_inconclusive() -> None:
    labels = tuple(
        generate_outcome_label(
            f"candidate-{index}",
            extract_token_outcome(
                f"token-{index}", start_slot=1, end_slot=2,
                start_value=100, end_value=end_value,
            ),
            "24h",
            success_delta=10,
            failure_delta=-10,
        )
        for index, end_value in enumerate((120, 80, 110, 100), start=1)
    )
    result = analyze_precision_recall(
        labels, ("candidate-1", "candidate-2"), "24h"
    )
    assert (result.true_positive, result.false_positive, result.false_negative) == (1, 1, 1)
    assert result.precision_bps == 5000
    assert result.recall_bps == 5000
    assert result == analyze_precision_recall(
        labels, ("candidate-1", "candidate-2"), "24h"
    )


def test_false_positive_analysis_is_canonical_and_replay_stable() -> None:
    label = build_candidate_quality_label(
        "candidate-1", "outcome-1", "24h", CandidateLabel.FAILED, "failed"
    )
    causes = (FalsePositiveCause.WASH_TRADE, FalsePositiveCause.INCOMPLETE_DATA)
    analysis = analyze_false_positive(label, causes)
    replayed = analyze_false_positive(label, tuple(reversed(causes)))
    assert analysis == replayed
    assert analysis.primary_cause is FalsePositiveCause.INCOMPLETE_DATA
    assert analysis.causes == (
        FalsePositiveCause.INCOMPLETE_DATA,
        FalsePositiveCause.WASH_TRADE,
    )


def test_false_positive_analysis_rejects_non_failed_and_duplicate_causes() -> None:
    label = build_candidate_quality_label(
        "candidate-1", "outcome-1", "24h", CandidateLabel.VALIDATED, "validated"
    )
    try:
        analyze_false_positive(label, (FalsePositiveCause.UNKNOWN,))
    except ValueError:
        pass
    else:
        raise AssertionError("validated labels cannot be false-positive analyses")


def test_confidence_calibration_report_is_deterministic() -> None:
    observations = (
        (8000, CandidateLabel.VALIDATED),
        (6000, CandidateLabel.FAILED),
        (7000, CandidateLabel.VALIDATED),
        (5000, CandidateLabel.INCONCLUSIVE),
    )
    report = build_confidence_calibration_report("24h", observations)
    assert report.sample_count == 4
    assert report.mean_raw_score_bps == 6500
    assert report.observed_success_bps == 5000
    assert report.calibration_error_bps == 1500
    assert report == build_confidence_calibration_report("24h", observations)


def test_confidence_calibration_report_rejects_invalid_scores() -> None:
    try:
        build_confidence_calibration_report(
            "24h", ((10001, CandidateLabel.VALIDATED),)
        )
    except (TypeError, ValueError):
        pass
    else:
        raise AssertionError("out-of-range score must fail closed")


def test_wallet_cohort_performance_is_deterministic() -> None:
    labels = tuple(
        generate_outcome_label(
            f"candidate-{index}",
            extract_token_outcome(
                f"token-{index}", start_slot=1, end_slot=2,
                start_value=100, end_value=end_value,
            ),
            "24h",
            success_delta=10,
            failure_delta=-10,
        )
        for index, end_value in enumerate((120, 80, 100), start=1)
    )
    performance = analyze_wallet_cohort_performance("cohort-a", "24h", labels)
    assert (
        performance.sample_count,
        performance.validated_count,
        performance.failed_count,
        performance.inconclusive_count,
        performance.success_rate_bps,
    ) == (3, 1, 1, 1, 3333)
    assert performance == analyze_wallet_cohort_performance("cohort-a", "24h", labels)


def test_token_lifecycle_performance_is_deterministic() -> None:
    labels = tuple(
        generate_outcome_label(
            f"candidate-{index}",
            extract_token_outcome(
                f"token-{index}", start_slot=1, end_slot=2,
                start_value=100, end_value=end_value,
            ),
            "24h",
            success_delta=10,
            failure_delta=-10,
        )
        for index, end_value in enumerate((120, 80, 100, 130), start=1)
    )
    performance = analyze_token_lifecycle_performance(
        "FirstMeaningfulSwap", "24h", labels
    )
    assert (
        performance.sample_count,
        performance.validated_count,
        performance.failed_count,
        performance.inconclusive_count,
        performance.success_rate_bps,
    ) == (4, 2, 1, 1, 5000)
    assert performance == analyze_token_lifecycle_performance(
        "FirstMeaningfulSwap", "24h", labels
    )


def test_walk_forward_dashboard_and_governance_gate() -> None:
    labels = tuple(
        generate_outcome_label(
            f"candidate-{index}",
            extract_token_outcome(
                f"token-{index}", start_slot=1, end_slot=2,
                start_value=100, end_value=end_value,
            ),
            "24h", success_delta=10, failure_delta=-10,
        )
        for index, end_value in enumerate((120, 80, 100), start=1)
    )
    cohort = analyze_wallet_cohort_performance("cohort-a", "24h", labels)
    lifecycle = analyze_token_lifecycle_performance("FirstLiquidity", "24h", labels)
    stability = evaluate_walk_forward_stability((cohort, lifecycle), tolerance_bps=1)
    assert stability.stable
    dashboard = build_candidate_quality_dashboard("24h", (cohort,), (lifecycle,))
    assert dashboard.mean_success_rate_bps == 3333
    calibration = build_confidence_calibration_report(
        "24h", ((8000, CandidateLabel.VALIDATED), (6000, CandidateLabel.FAILED))
    )
    gate = evaluate_calibration_governance_gate(calibration, max_error_bps=1000)
    assert not gate.passed
