"""Point-in-time integer price evidence and maturity-gated candidate outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from smart_money.application.candidate_quality import (
    CalibrationGovernanceGate,
    CandidateLabel,
    CandidateQualityLabel,
    ConfidenceCalibrationReport,
    PrecisionRecallWindow,
    analyze_precision_recall,
    build_candidate_quality_label,
    build_confidence_calibration_report,
    evaluate_calibration_governance_gate,
)
from smart_money.core.ids import deterministic_id


class OutcomeCollectionStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETE = "COMPLETE"


@dataclass(frozen=True, slots=True)
class PointInTimePriceEvidence:
    mint: str
    quote_mint: str
    observed_at: int
    slot: int
    asset_amount_raw: int
    quote_value_raw: int
    source_id: str
    evidence_id: str
    schema_version: str = "point_in_time_price_evidence.v1"

    def __post_init__(self) -> None:
        for name in ("mint", "quote_mint", "source_id", "evidence_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        for name in ("observed_at", "slot", "asset_amount_raw", "quote_value_raw"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if not self.asset_amount_raw or not self.quote_value_raw:
            raise ValueError("price evidence amounts must be positive")
        if self.evidence_id != deterministic_id("point-in-time-price", self.identity_payload()):
            raise ValueError("evidence_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, object]:
        return {
            "asset_amount_raw": self.asset_amount_raw,
            "mint": self.mint,
            "observed_at": self.observed_at,
            "quote_mint": self.quote_mint,
            "quote_value_raw": self.quote_value_raw,
            "schema_version": self.schema_version,
            "slot": self.slot,
            "source_id": self.source_id,
        }

    def canonical_dict(self) -> dict[str, object]:
        return {"evidence_id": self.evidence_id, **self.identity_payload()}


def build_point_in_time_price_evidence(
    *,
    mint: str,
    quote_mint: str,
    observed_at: int,
    slot: int,
    asset_amount_raw: int,
    quote_value_raw: int,
    source_id: str,
) -> PointInTimePriceEvidence:
    identity = {
        "asset_amount_raw": asset_amount_raw,
        "mint": mint.strip(),
        "observed_at": observed_at,
        "quote_mint": quote_mint.strip(),
        "quote_value_raw": quote_value_raw,
        "schema_version": "point_in_time_price_evidence.v1",
        "slot": slot,
        "source_id": source_id.strip(),
    }
    return PointInTimePriceEvidence(
        evidence_id=deterministic_id("point-in-time-price", identity), **identity
    )


@dataclass(frozen=True, slots=True)
class CandidateOutcomeWindow:
    candidate_id: str
    horizon_hours: int
    status: OutcomeCollectionStatus
    start_evidence_id: str
    end_evidence_id: str | None
    return_bps: int | None
    outcome_id: str
    schema_version: str = "candidate_outcome_window.v1"

    def identity_payload(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "end_evidence_id": self.end_evidence_id,
            "horizon_hours": self.horizon_hours,
            "return_bps": self.return_bps,
            "schema_version": self.schema_version,
            "start_evidence_id": self.start_evidence_id,
            "status": self.status.value,
        }

    def canonical_dict(self) -> dict[str, object]:
        return {"outcome_id": self.outcome_id, **self.identity_payload()}


def collect_candidate_outcome(
    candidate_id: str,
    start: PointInTimePriceEvidence,
    end: PointInTimePriceEvidence | None,
    *,
    horizon_hours: int,
    as_of: int,
) -> CandidateOutcomeWindow:
    if horizon_hours not in {24, 72}:
        raise ValueError("supported outcome horizons are 24h and 72h")
    if not isinstance(as_of, int) or isinstance(as_of, bool) or as_of < start.observed_at:
        raise ValueError("as_of must not precede start evidence")
    mature_at = start.observed_at + horizon_hours * 3600
    complete = as_of >= mature_at and end is not None
    if end is not None:
        if end.mint != start.mint or end.quote_mint != start.quote_mint:
            raise ValueError("outcome price identities do not match")
        if end.observed_at < mature_at:
            raise ValueError("end evidence precedes outcome maturity")
    return_bps = None
    if complete:
        assert end is not None
        start_cross = start.quote_value_raw * end.asset_amount_raw
        end_cross = end.quote_value_raw * start.asset_amount_raw
        return_bps = (end_cross * 10000 // start_cross) - 10000
    identity = {
        "candidate_id": candidate_id.strip(),
        "end_evidence_id": end.evidence_id if complete and end else None,
        "horizon_hours": horizon_hours,
        "return_bps": return_bps,
        "schema_version": "candidate_outcome_window.v1",
        "start_evidence_id": start.evidence_id,
        "status": (OutcomeCollectionStatus.COMPLETE if complete else OutcomeCollectionStatus.PENDING).value,
    }
    return CandidateOutcomeWindow(
        candidate_id=candidate_id.strip(),
        horizon_hours=horizon_hours,
        status=OutcomeCollectionStatus(identity["status"]),
        start_evidence_id=start.evidence_id,
        end_evidence_id=identity["end_evidence_id"],
        return_bps=return_bps,
        outcome_id=deterministic_id("candidate-outcome-window", identity),
    )


def verify_candidate_outcome_replay(
    expected: CandidateOutcomeWindow,
    start: PointInTimePriceEvidence,
    end: PointInTimePriceEvidence | None,
    *,
    as_of: int,
) -> bool:
    replayed = collect_candidate_outcome(
        expected.candidate_id,
        start,
        end,
        horizon_hours=expected.horizon_hours,
        as_of=as_of,
    )
    return replayed == expected


@dataclass(frozen=True, slots=True)
class OutcomeCalibrationResult:
    labels: tuple[CandidateQualityLabel, ...]
    precision_recall: PrecisionRecallWindow
    calibration: ConfidenceCalibrationReport
    governance_gate: CalibrationGovernanceGate
    result_id: str
    schema_version: str = "outcome_calibration_result.v1"


def calibrate_completed_outcomes(
    outcomes: tuple[CandidateOutcomeWindow, ...],
    *,
    predicted_scores_bps: dict[str, int],
    success_return_bps: int,
    failure_return_bps: int,
    max_calibration_error_bps: int,
) -> OutcomeCalibrationResult:
    complete = tuple(item for item in outcomes if item.status is OutcomeCollectionStatus.COMPLETE)
    if not complete:
        raise ValueError("calibration requires completed outcomes")
    if failure_return_bps >= success_return_bps:
        raise ValueError("failure threshold must be below success threshold")
    horizon = f"{complete[0].horizon_hours}h"
    if any(f"{item.horizon_hours}h" != horizon for item in complete):
        raise ValueError("calibration outcomes must share one horizon")
    labels = []
    for item in complete:
        assert item.return_bps is not None
        if item.return_bps >= success_return_bps:
            label = CandidateLabel.VALIDATED
        elif item.return_bps <= failure_return_bps:
            label = CandidateLabel.FAILED
        else:
            label = CandidateLabel.INCONCLUSIVE
        labels.append(
            build_candidate_quality_label(
                item.candidate_id,
                item.outcome_id,
                horizon,
                label,
                f"return_bps={item.return_bps}",
            )
        )
    label_tuple = tuple(labels)
    predicted = tuple(sorted(candidate_id for candidate_id in predicted_scores_bps if candidate_id in {item.candidate_id for item in complete}))
    precision_recall = analyze_precision_recall(label_tuple, predicted, horizon)
    observations = tuple(
        (predicted_scores_bps[item.candidate_id], label.label)
        for item, label in zip(complete, label_tuple, strict=True)
        if item.candidate_id in predicted_scores_bps
    )
    calibration = build_confidence_calibration_report(horizon, observations)
    gate = evaluate_calibration_governance_gate(
        calibration, max_error_bps=max_calibration_error_bps
    )
    identity = {
        "gate_id": gate.gate_id,
        "label_ids": tuple(item.label_id for item in label_tuple),
        "precision_recall_id": precision_recall.analysis_id,
        "report_id": calibration.report_id,
        "schema_version": "outcome_calibration_result.v1",
    }
    return OutcomeCalibrationResult(
        label_tuple,
        precision_recall,
        calibration,
        gate,
        deterministic_id("outcome-calibration-result", identity),
    )


__all__ = [
    "CandidateOutcomeWindow",
    "OutcomeCalibrationResult",
    "OutcomeCollectionStatus",
    "PointInTimePriceEvidence",
    "build_point_in_time_price_evidence",
    "calibrate_completed_outcomes",
    "collect_candidate_outcome",
    "verify_candidate_outcome_replay",
]
