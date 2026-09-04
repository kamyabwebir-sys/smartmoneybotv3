from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload


def consolidate_candidate_evidence(payloads: tuple[EvidencePayload, ...]) -> tuple[EvidencePayload, ...]:
    if not isinstance(payloads, tuple) or not all(isinstance(x, EvidencePayload) for x in payloads):
        raise TypeError("payloads must be tuple of EvidencePayload")
    unique = {item.get_canonical_id(): item for item in payloads}
    return tuple(unique[key] for key in sorted(unique))


def verify_candidate_feature_replay(features: tuple[dict[str, Any], ...],
                                     replayed: tuple[dict[str, Any], ...]) -> bool:
    return features == replayed


@dataclass(frozen=True, slots=True)
class HistoricalOutcomeBinding:
    candidate_id: str
    outcome_id: str
    binding_id: str


def bind_historical_outcome(candidate_id: str, outcome_id: str) -> HistoricalOutcomeBinding:
    identity = {"candidate_id": candidate_id.strip(), "outcome_id": outcome_id.strip(),
                "schema_version": "historical_outcome_binding.v1"}
    return HistoricalOutcomeBinding(candidate_id, outcome_id,
                                    deterministic_id("historical_outcome_binding", identity))


@dataclass(frozen=True, slots=True)
class PrecisionRecallEvidence:
    true_positive: int
    false_positive: int
    false_negative: int
    precision_bps: int
    recall_bps: int
    evidence_id: str


def evaluate_precision_recall(true_positive: int, false_positive: int,
                              false_negative: int) -> PrecisionRecallEvidence:
    if min(true_positive, false_positive, false_negative) < 0:
        raise ValueError("counts must be non-negative")
    precision = true_positive * 10000 // (true_positive + false_positive) if true_positive + false_positive else 0
    recall = true_positive * 10000 // (true_positive + false_negative) if true_positive + false_negative else 0
    identity = {"false_negative": false_negative, "false_positive": false_positive,
                "precision_bps": precision, "recall_bps": recall,
                "schema_version": "precision_recall_evidence.v1", "true_positive": true_positive}
    return PrecisionRecallEvidence(true_positive, false_positive, false_negative, precision, recall,
                                   deterministic_id("precision_recall_evidence", identity))


def classify_false_positive(predicted: bool, realized: bool) -> str:
    return "FALSE_POSITIVE" if predicted and not realized else "VALIDATED" if predicted and realized else "NOT_PREDICTED"


@dataclass(frozen=True, slots=True)
class ConfidenceCalibration:
    raw_score_bps: int
    calibrated_score_bps: int
    calibration_id: str


def calibrate_confidence(raw_score_bps: int, sample_success_bps: int) -> ConfidenceCalibration:
    if not 0 <= raw_score_bps <= 10000 or not 0 <= sample_success_bps <= 10000:
        raise ValueError("scores must be between 0 and 10000")
    identity = {"raw_score_bps": raw_score_bps, "sample_success_bps": sample_success_bps,
                "schema_version": "confidence_calibration.v1"}
    return ConfidenceCalibration(raw_score_bps, (raw_score_bps + sample_success_bps) // 2,
                                 deterministic_id("confidence_calibration", identity))


@dataclass(frozen=True, slots=True)
class HistoricalBackfill:
    subject_ids: tuple[str, ...]
    from_slot: int
    to_slot: int
    backfill_id: str


def build_historical_backfill(subject_ids: tuple[str, ...], from_slot: int, to_slot: int) -> HistoricalBackfill:
    if not subject_ids or from_slot < 0 or to_slot < from_slot:
        raise ValueError("invalid backfill")
    identity = {"from_slot": from_slot, "schema_version": "historical_backfill.v1",
                "subject_ids": subject_ids, "to_slot": to_slot}
    return HistoricalBackfill(subject_ids, from_slot, to_slot,
                              deterministic_id("historical_backfill", identity))


@dataclass(frozen=True, slots=True)
class CandidateReplaySession:
    candidate_ids: tuple[str, ...]
    replay_id: str


def build_candidate_replay_session(candidate_ids: tuple[str, ...]) -> CandidateReplaySession:
    identity = {"candidate_ids": candidate_ids, "schema_version": "candidate_replay_session.v1"}
    return CandidateReplaySession(candidate_ids, deterministic_id("candidate_replay_session", identity))


@dataclass(frozen=True, slots=True)
class CandidateDashboardAudit:
    row_count: int
    dashboard_id: str
    audit_id: str


def audit_candidate_dashboard(dashboard_id: str, row_count: int) -> CandidateDashboardAudit:
    identity = {"dashboard_id": dashboard_id.strip(), "row_count": row_count,
                "schema_version": "candidate_dashboard_audit.v1"}
    return CandidateDashboardAudit(row_count, dashboard_id,
                                   deterministic_id("candidate_dashboard_audit", identity))


def verify_production_release_gate(checks: tuple[str, ...], passed: tuple[str, ...]) -> bool:
    return bool(checks) and set(checks).issubset(passed)


__all__ = [
    "consolidate_candidate_evidence", "verify_candidate_feature_replay",
    "HistoricalOutcomeBinding", "bind_historical_outcome", "PrecisionRecallEvidence",
    "evaluate_precision_recall", "classify_false_positive", "ConfidenceCalibration",
    "calibrate_confidence", "HistoricalBackfill", "build_historical_backfill",
    "CandidateReplaySession", "build_candidate_replay_session", "CandidateDashboardAudit",
    "audit_candidate_dashboard", "verify_production_release_gate",
]
