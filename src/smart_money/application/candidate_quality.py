from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from smart_money.application.outcome_learning import OutcomeObservation
from smart_money.core.ids import deterministic_id


class CandidateLabel(str, Enum):
    VALIDATED = "VALIDATED"
    FAILED = "FAILED"
    INCONCLUSIVE = "INCONCLUSIVE"


class FalsePositiveCause(str, Enum):
    WASH_TRADE = "WASH_TRADE"
    INSUFFICIENT_LIQUIDITY = "INSUFFICIENT_LIQUIDITY"
    IDENTITY_CONFLICT = "IDENTITY_CONFLICT"
    INCOMPLETE_DATA = "INCOMPLETE_DATA"
    DECODER_ERROR = "DECODER_ERROR"
    LIFECYCLE_FAILURE = "LIFECYCLE_FAILURE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class CandidateQualityLabel:
    candidate_id: str
    outcome_id: str
    horizon: str
    label: CandidateLabel
    rationale: str
    label_id: str
    schema_version: str = "candidate_quality_label.v1"


@dataclass(frozen=True, slots=True)
class PrecisionRecallWindow:
    horizon: str
    true_positive: int
    false_positive: int
    false_negative: int
    precision_bps: int
    recall_bps: int
    analysis_id: str
    schema_version: str = "precision_recall_window.v1"


@dataclass(frozen=True, slots=True)
class FalsePositiveAnalysis:
    candidate_id: str
    label_id: str
    causes: tuple[FalsePositiveCause, ...]
    primary_cause: FalsePositiveCause
    analysis_id: str
    schema_version: str = "false_positive_analysis.v1"


@dataclass(frozen=True, slots=True)
class ConfidenceCalibrationReport:
    horizon: str
    sample_count: int
    mean_raw_score_bps: int
    observed_success_bps: int
    calibration_error_bps: int
    report_id: str
    schema_version: str = "confidence_calibration_report.v1"


@dataclass(frozen=True, slots=True)
class WalletCohortPerformance:
    cohort_id: str
    horizon: str
    sample_count: int
    validated_count: int
    failed_count: int
    inconclusive_count: int
    success_rate_bps: int
    performance_id: str
    schema_version: str = "wallet_cohort_performance.v1"


@dataclass(frozen=True, slots=True)
class TokenLifecyclePerformance:
    lifecycle_phase: str
    horizon: str
    sample_count: int
    validated_count: int
    failed_count: int
    inconclusive_count: int
    success_rate_bps: int
    performance_id: str
    schema_version: str = "token_lifecycle_performance.v1"


@dataclass(frozen=True, slots=True)
class WalkForwardStability:
    window_ids: tuple[str, ...]
    stable: bool
    min_success_rate_bps: int
    max_success_rate_bps: int
    stability_id: str
    schema_version: str = "walk_forward_stability.v1"


@dataclass(frozen=True, slots=True)
class CandidateQualityDashboard:
    horizon: str
    cohort_count: int
    lifecycle_count: int
    mean_success_rate_bps: int
    dashboard_id: str
    schema_version: str = "candidate_quality_dashboard.v1"


@dataclass(frozen=True, slots=True)
class CalibrationGovernanceGate:
    report_id: str
    max_error_bps: int
    calibration_error_bps: int
    passed: bool
    gate_id: str
    schema_version: str = "calibration_governance_gate.v1"


def build_candidate_quality_label(
    candidate_id: str,
    outcome_id: str,
    horizon: str,
    label: CandidateLabel,
    rationale: str,
) -> CandidateQualityLabel:
    values = (candidate_id, outcome_id, horizon, rationale)
    if not all(isinstance(value, str) and value.strip() for value in values):
        raise ValueError("candidate label text fields must be non-empty")
    if not isinstance(label, CandidateLabel):
        raise TypeError("label must be CandidateLabel")
    identity = {
        "candidate_id": candidate_id.strip(),
        "outcome_id": outcome_id.strip(),
        "horizon": horizon.strip(),
        "label": label.value,
        "rationale": rationale.strip(),
        "schema_version": "candidate_quality_label.v1",
    }
    return CandidateQualityLabel(
        candidate_id.strip(), outcome_id.strip(), horizon.strip(), label,
        rationale.strip(), deterministic_id("candidate-quality-label", identity),
    )


def generate_outcome_label(
    candidate_id: str,
    observation: OutcomeObservation,
    horizon: str,
    *,
    success_delta: int = 1,
    failure_delta: int = -1,
) -> CandidateQualityLabel:
    if not isinstance(observation, OutcomeObservation):
        raise TypeError("observation must be OutcomeObservation")
    if isinstance(success_delta, bool) or not isinstance(success_delta, int):
        raise TypeError("success_delta must be an integer")
    if isinstance(failure_delta, bool) or not isinstance(failure_delta, int):
        raise TypeError("failure_delta must be an integer")
    if failure_delta >= success_delta:
        raise ValueError("failure_delta must be less than success_delta")

    delta = observation.end_value - observation.start_value
    if delta >= success_delta:
        label = CandidateLabel.VALIDATED
        rationale = f"outcome_delta={delta};threshold>={success_delta}"
    elif delta <= failure_delta:
        label = CandidateLabel.FAILED
        rationale = f"outcome_delta={delta};threshold<={failure_delta}"
    else:
        label = CandidateLabel.INCONCLUSIVE
        rationale = (
            f"outcome_delta={delta};neutral_band="
            f"({failure_delta},{success_delta})"
        )
    return build_candidate_quality_label(
        candidate_id, observation.outcome_id, horizon, label, rationale
    )


def analyze_precision_recall(
    labels: tuple[CandidateQualityLabel, ...],
    predicted_candidate_ids: tuple[str, ...],
    horizon: str,
) -> PrecisionRecallWindow:
    if not isinstance(labels, tuple) or not all(
        isinstance(item, CandidateQualityLabel) for item in labels
    ):
        raise TypeError("labels must be tuple of CandidateQualityLabel")
    if not isinstance(predicted_candidate_ids, tuple) or not all(
        isinstance(item, str) and item.strip() for item in predicted_candidate_ids
    ):
        raise TypeError("predicted_candidate_ids must be tuple of non-empty strings")
    if not isinstance(horizon, str) or not horizon.strip():
        raise ValueError("horizon must be non-empty")
    if len(set(predicted_candidate_ids)) != len(predicted_candidate_ids):
        raise ValueError("predicted_candidate_ids must be unique")

    relevant = {
        item.candidate_id: item
        for item in labels
        if item.horizon == horizon and item.label is not CandidateLabel.INCONCLUSIVE
    }
    predicted = {item.strip() for item in predicted_candidate_ids}
    actual_positive = {
        candidate_id
        for candidate_id, item in relevant.items()
        if item.label is CandidateLabel.VALIDATED
    }
    true_positive = len(predicted & actual_positive)
    false_positive = len(predicted - actual_positive)
    false_negative = len(actual_positive - predicted)
    precision_bps = (
        true_positive * 10000 // (true_positive + false_positive)
        if true_positive + false_positive
        else 0
    )
    recall_bps = (
        true_positive * 10000 // (true_positive + false_negative)
        if true_positive + false_negative
        else 0
    )
    identity = {
        "false_negative": false_negative,
        "false_positive": false_positive,
        "horizon": horizon.strip(),
        "label_ids": tuple(sorted(item.label_id for item in labels if item.horizon == horizon)),
        "precision_bps": precision_bps,
        "predicted_candidate_ids": tuple(sorted(predicted)),
        "recall_bps": recall_bps,
        "schema_version": "precision_recall_window.v1",
        "true_positive": true_positive,
    }
    return PrecisionRecallWindow(
        horizon.strip(), true_positive, false_positive, false_negative,
        precision_bps, recall_bps, deterministic_id("precision-recall-window", identity),
    )


def analyze_false_positive(
    label: CandidateQualityLabel,
    causes: tuple[FalsePositiveCause, ...],
) -> FalsePositiveAnalysis:
    if not isinstance(label, CandidateQualityLabel):
        raise TypeError("label must be CandidateQualityLabel")
    if label.label is not CandidateLabel.FAILED:
        raise ValueError("false-positive analysis requires a FAILED label")
    if not isinstance(causes, tuple) or not causes:
        raise ValueError("causes must be a non-empty tuple")
    if not all(isinstance(cause, FalsePositiveCause) for cause in causes):
        raise TypeError("causes must contain FalsePositiveCause values")
    if len(set(causes)) != len(causes):
        raise ValueError("causes must be unique")
    ordered = tuple(sorted(causes, key=lambda cause: cause.value))
    identity = {
        "candidate_id": label.candidate_id,
        "causes": tuple(cause.value for cause in ordered),
        "label_id": label.label_id,
        "schema_version": "false_positive_analysis.v1",
    }
    return FalsePositiveAnalysis(
        label.candidate_id,
        label.label_id,
        ordered,
        ordered[0],
        deterministic_id("false-positive-analysis", identity),
    )


def build_confidence_calibration_report(
    horizon: str,
    observations: tuple[tuple[int, CandidateLabel], ...],
) -> ConfidenceCalibrationReport:
    if not isinstance(horizon, str) or not horizon.strip():
        raise ValueError("horizon must be non-empty")
    if not isinstance(observations, tuple) or not observations:
        raise ValueError("observations must be a non-empty tuple")
    for item in observations:
        if (
            not isinstance(item, tuple)
            or len(item) != 2
            or isinstance(item[0], bool)
            or not isinstance(item[0], int)
            or not 0 <= item[0] <= 10000
            or not isinstance(item[1], CandidateLabel)
        ):
            raise TypeError("observations must contain (score_bps, CandidateLabel)")
    sample_count = len(observations)
    mean_raw_score_bps = sum(item[0] for item in observations) // sample_count
    observed_success_bps = (
        sum(item[1] is CandidateLabel.VALIDATED for item in observations)
        * 10000
        // sample_count
    )
    calibration_error_bps = abs(mean_raw_score_bps - observed_success_bps)
    identity = {
        "horizon": horizon.strip(),
        "observations": tuple(
            (score, label.value) for score, label in observations
        ),
        "schema_version": "confidence_calibration_report.v1",
    }
    return ConfidenceCalibrationReport(
        horizon.strip(),
        sample_count,
        mean_raw_score_bps,
        observed_success_bps,
        calibration_error_bps,
        deterministic_id("confidence-calibration-report", identity),
    )


def analyze_wallet_cohort_performance(
    cohort_id: str,
    horizon: str,
    labels: tuple[CandidateQualityLabel, ...],
) -> WalletCohortPerformance:
    for value, name in ((cohort_id, "cohort_id"), (horizon, "horizon")):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be non-empty")
    if not isinstance(labels, tuple) or not labels:
        raise ValueError("labels must be a non-empty tuple")
    if not all(isinstance(item, CandidateQualityLabel) for item in labels):
        raise TypeError("labels must contain CandidateQualityLabel values")
    relevant = tuple(item for item in labels if item.horizon == horizon.strip())
    if not relevant:
        raise ValueError("no labels for requested horizon")
    sample_count = len(relevant)
    validated_count = sum(item.label is CandidateLabel.VALIDATED for item in relevant)
    failed_count = sum(item.label is CandidateLabel.FAILED for item in relevant)
    inconclusive_count = sum(
        item.label is CandidateLabel.INCONCLUSIVE for item in relevant
    )
    success_rate_bps = validated_count * 10000 // sample_count
    identity = {
        "cohort_id": cohort_id.strip(),
        "horizon": horizon.strip(),
        "label_ids": tuple(sorted(item.label_id for item in relevant)),
        "schema_version": "wallet_cohort_performance.v1",
    }
    return WalletCohortPerformance(
        cohort_id.strip(),
        horizon.strip(),
        sample_count,
        validated_count,
        failed_count,
        inconclusive_count,
        success_rate_bps,
        deterministic_id("wallet-cohort-performance", identity),
    )


def analyze_token_lifecycle_performance(
    lifecycle_phase: str,
    horizon: str,
    labels: tuple[CandidateQualityLabel, ...],
) -> TokenLifecyclePerformance:
    for value, name in ((lifecycle_phase, "lifecycle_phase"), (horizon, "horizon")):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be non-empty")
    if not isinstance(labels, tuple) or not labels:
        raise ValueError("labels must be a non-empty tuple")
    if not all(isinstance(item, CandidateQualityLabel) for item in labels):
        raise TypeError("labels must contain CandidateQualityLabel values")
    relevant = tuple(item for item in labels if item.horizon == horizon.strip())
    if not relevant:
        raise ValueError("no labels for requested horizon")
    sample_count = len(relevant)
    validated_count = sum(item.label is CandidateLabel.VALIDATED for item in relevant)
    failed_count = sum(item.label is CandidateLabel.FAILED for item in relevant)
    inconclusive_count = sum(
        item.label is CandidateLabel.INCONCLUSIVE for item in relevant
    )
    success_rate_bps = validated_count * 10000 // sample_count
    identity = {
        "horizon": horizon.strip(),
        "label_ids": tuple(sorted(item.label_id for item in relevant)),
        "lifecycle_phase": lifecycle_phase.strip(),
        "schema_version": "token_lifecycle_performance.v1",
    }
    return TokenLifecyclePerformance(
        lifecycle_phase.strip(),
        horizon.strip(),
        sample_count,
        validated_count,
        failed_count,
        inconclusive_count,
        success_rate_bps,
        deterministic_id("token-lifecycle-performance", identity),
    )


def evaluate_walk_forward_stability(
    windows: tuple[WalletCohortPerformance | TokenLifecyclePerformance, ...],
    *,
    tolerance_bps: int = 1000,
) -> WalkForwardStability:
    if not isinstance(windows, tuple) or not windows:
        raise ValueError("windows must be a non-empty tuple")
    if not all(
        isinstance(item, (WalletCohortPerformance, TokenLifecyclePerformance))
        for item in windows
    ):
        raise TypeError("windows must contain performance records")
    if isinstance(tolerance_bps, bool) or not isinstance(tolerance_bps, int):
        raise TypeError("tolerance_bps must be an integer")
    if not 0 <= tolerance_bps <= 10000:
        raise ValueError("tolerance_bps must be between 0 and 10000")
    rates = tuple(item.success_rate_bps for item in windows)
    minimum, maximum = min(rates), max(rates)
    identity = {
        "rates": rates,
        "tolerance_bps": tolerance_bps,
        "window_ids": tuple(
            item.performance_id for item in windows
        ),
        "schema_version": "walk_forward_stability.v1",
    }
    return WalkForwardStability(
        tuple(item.performance_id for item in windows),
        maximum - minimum <= tolerance_bps,
        minimum,
        maximum,
        deterministic_id("walk-forward-stability", identity),
    )


def build_candidate_quality_dashboard(
    horizon: str,
    cohorts: tuple[WalletCohortPerformance, ...],
    lifecycles: tuple[TokenLifecyclePerformance, ...],
) -> CandidateQualityDashboard:
    if not isinstance(horizon, str) or not horizon.strip():
        raise ValueError("horizon must be non-empty")
    if not isinstance(cohorts, tuple) or not isinstance(lifecycles, tuple):
        raise TypeError("cohorts and lifecycles must be tuples")
    if not all(isinstance(item, WalletCohortPerformance) for item in cohorts):
        raise TypeError("cohorts must contain WalletCohortPerformance values")
    if not all(isinstance(item, TokenLifecyclePerformance) for item in lifecycles):
        raise TypeError("lifecycles must contain TokenLifecyclePerformance values")
    rows = cohorts + lifecycles
    if not rows or any(item.horizon != horizon.strip() for item in rows):
        raise ValueError("dashboard requires matching non-empty horizon rows")
    mean_rate = sum(item.success_rate_bps for item in rows) // len(rows)
    identity = {
        "horizon": horizon.strip(),
        "cohort_ids": tuple(item.performance_id for item in cohorts),
        "lifecycle_ids": tuple(item.performance_id for item in lifecycles),
        "schema_version": "candidate_quality_dashboard.v1",
    }
    return CandidateQualityDashboard(
        horizon.strip(), len(cohorts), len(lifecycles), mean_rate,
        deterministic_id("candidate-quality-dashboard", identity),
    )


def evaluate_calibration_governance_gate(
    report: ConfidenceCalibrationReport,
    *,
    max_error_bps: int,
) -> CalibrationGovernanceGate:
    if not isinstance(report, ConfidenceCalibrationReport):
        raise TypeError("report must be ConfidenceCalibrationReport")
    if isinstance(max_error_bps, bool) or not isinstance(max_error_bps, int):
        raise TypeError("max_error_bps must be an integer")
    if not 0 <= max_error_bps <= 10000:
        raise ValueError("max_error_bps must be between 0 and 10000")
    passed = report.calibration_error_bps <= max_error_bps
    identity = {
        "calibration_error_bps": report.calibration_error_bps,
        "max_error_bps": max_error_bps,
        "passed": passed,
        "report_id": report.report_id,
        "schema_version": "calibration_governance_gate.v1",
    }
    return CalibrationGovernanceGate(
        report.report_id, max_error_bps, report.calibration_error_bps, passed,
        deterministic_id("calibration-governance-gate", identity),
    )


__all__ = [
    "CandidateLabel",
    "CandidateQualityLabel",
    "FalsePositiveCause",
    "FalsePositiveAnalysis",
    "ConfidenceCalibrationReport",
    "WalletCohortPerformance",
    "TokenLifecyclePerformance",
    "WalkForwardStability",
    "CandidateQualityDashboard",
    "CalibrationGovernanceGate",
    "PrecisionRecallWindow",
    "build_candidate_quality_label",
    "generate_outcome_label",
    "analyze_precision_recall",
    "analyze_false_positive",
    "build_confidence_calibration_report",
    "analyze_wallet_cohort_performance",
    "analyze_token_lifecycle_performance",
    "evaluate_walk_forward_stability",
    "build_candidate_quality_dashboard",
    "evaluate_calibration_governance_gate",
]
