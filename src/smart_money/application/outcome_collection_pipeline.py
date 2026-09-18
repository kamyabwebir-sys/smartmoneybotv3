"""Maturity scheduling, dataset materialization and human-gated calibration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

from smart_money.application.point_in_time_outcome import (
    CandidateOutcomeWindow,
    OutcomeCalibrationResult,
    PointInTimePriceEvidence,
    calibrate_completed_outcomes,
    collect_candidate_outcome,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class OutcomeCollectionJob:
    candidate_id: str
    horizon_hours: int
    due_at: int
    start_evidence_id: str
    job_id: str
    schema_version: str = "outcome_collection_job.v1"

    def canonical_dict(self) -> dict[str, object]:
        return asdict(self)


def schedule_outcomes(
    candidate_id: str, start: PointInTimePriceEvidence
) -> tuple[OutcomeCollectionJob, ...]:
    jobs = []
    for horizon in (24, 72):
        identity = {
            "candidate_id": candidate_id.strip(), "due_at": start.observed_at + horizon * 3600,
            "horizon_hours": horizon, "schema_version": "outcome_collection_job.v1",
            "start_evidence_id": start.evidence_id,
        }
        jobs.append(OutcomeCollectionJob(job_id=deterministic_id("outcome-collection-job", identity), **identity))
    return tuple(jobs)


def run_due_outcome_job(
    job: OutcomeCollectionJob,
    start: PointInTimePriceEvidence,
    end: PointInTimePriceEvidence | None,
    *,
    as_of: int,
) -> CandidateOutcomeWindow:
    if job.start_evidence_id != start.evidence_id:
        raise ValueError("job is not linked to start price evidence")
    return collect_candidate_outcome(
        job.candidate_id, start, end, horizon_hours=job.horizon_hours, as_of=as_of
    )


@dataclass(frozen=True, slots=True)
class OutcomeDataset:
    split: str
    horizon_hours: int
    outcomes: tuple[CandidateOutcomeWindow, ...]
    dataset_id: str
    schema_version: str = "mainnet_outcome_dataset.v1"

    def canonical_dict(self) -> dict[str, object]:
        return {
            "dataset_id": self.dataset_id, "horizon_hours": self.horizon_hours,
            "items": tuple(item.canonical_dict() for item in self.outcomes),
            "schema_version": self.schema_version, "split": self.split,
        }


def materialize_outcome_dataset(
    outcomes: tuple[CandidateOutcomeWindow, ...], *, split: str
) -> OutcomeDataset:
    if split not in {"calibration", "evaluation"}:
        raise ValueError("dataset split must be calibration or evaluation")
    if not outcomes or any(item.return_bps is None for item in outcomes):
        raise ValueError("dataset requires completed outcomes")
    horizon = outcomes[0].horizon_hours
    if any(item.horizon_hours != horizon for item in outcomes):
        raise ValueError("dataset outcomes must share one horizon")
    ordered = tuple(sorted(outcomes, key=lambda item: item.candidate_id))
    identity = {
        "horizon_hours": horizon, "outcome_ids": tuple(item.outcome_id for item in ordered),
        "schema_version": "mainnet_outcome_dataset.v1", "split": split,
    }
    return OutcomeDataset(split, horizon, ordered, deterministic_id("mainnet-outcome-dataset", identity))


class HumanCalibrationStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class HumanCalibrationReview:
    calibration_result_id: str
    reviewer: str
    status: HumanCalibrationStatus
    rationale: str
    review_id: str
    schema_version: str = "human_calibration_review.v1"

    def canonical_dict(self) -> dict[str, object]:
        return {**asdict(self), "status": self.status.value}


def review_calibration(
    result: OutcomeCalibrationResult,
    *, reviewer: str,
    approve: bool,
    rationale: str,
) -> HumanCalibrationReview:
    if not reviewer.strip() or not rationale.strip():
        raise ValueError("reviewer and rationale are required")
    status = HumanCalibrationStatus.APPROVED if approve and result.governance_gate.passed else HumanCalibrationStatus.REJECTED
    identity = {
        "calibration_result_id": result.result_id, "rationale": rationale.strip(),
        "reviewer": reviewer.strip(), "schema_version": "human_calibration_review.v1",
        "status": status.value,
    }
    return HumanCalibrationReview(
        result.result_id, reviewer.strip(), status, rationale.strip(),
        deterministic_id("human-calibration-review", identity),
    )


def calibrate_dataset(
    dataset: OutcomeDataset,
    *, predicted_scores_bps: dict[str, int],
    success_return_bps: int,
    failure_return_bps: int,
    max_calibration_error_bps: int,
) -> OutcomeCalibrationResult:
    if dataset.split != "calibration":
        raise ValueError("walk-forward calibration cannot fit the evaluation split")
    return calibrate_completed_outcomes(
        dataset.outcomes, predicted_scores_bps=predicted_scores_bps,
        success_return_bps=success_return_bps, failure_return_bps=failure_return_bps,
        max_calibration_error_bps=max_calibration_error_bps,
    )


__all__ = [
    "HumanCalibrationReview", "HumanCalibrationStatus", "OutcomeCollectionJob",
    "OutcomeDataset", "calibrate_dataset", "materialize_outcome_dataset",
    "review_calibration", "run_due_outcome_job", "schedule_outcomes",
]
