from __future__ import annotations
from dataclasses import dataclass
from smart_money.application.outcome_learning import OutcomeObservation, LearningReport
from smart_money.application.outcome_governance import WalkForwardPromotionEvidence
from smart_money.core.ids import deterministic_id

@dataclass(frozen=True, slots=True)
class OutcomeReadModel:
    rows: tuple[OutcomeObservation, ...]
    schema_version: str = "outcome_read_model.v1"

def build_outcome_read_model(rows: tuple[OutcomeObservation, ...]) -> OutcomeReadModel:
    if not isinstance(rows, tuple) or not all(isinstance(x, OutcomeObservation) for x in rows):
        raise TypeError("rows must be tuple of OutcomeObservation")
    return OutcomeReadModel(rows)

def query_outcomes(model: OutcomeReadModel, *, subject_id: str | None = None,
                   subject_kind: str | None = None) -> tuple[OutcomeObservation, ...]:
    if not isinstance(model, OutcomeReadModel):
        raise TypeError("model must be OutcomeReadModel")
    return tuple(x for x in model.rows if
                 (subject_id is None or x.subject_id == subject_id.strip()) and
                 (subject_kind is None or x.subject_kind == subject_kind))

@dataclass(frozen=True, slots=True)
class LearningReportQueryResult:
    rows: tuple[LearningReport, ...]
    query_id: str
    schema_version: str = "learning_report_query.v1"

def query_learning_reports(reports: tuple[LearningReport, ...], *,
                           min_success_count: int | None = None) -> LearningReportQueryResult:
    if not isinstance(reports, tuple) or not all(isinstance(x, LearningReport) for x in reports):
        raise TypeError("reports must be tuple of LearningReport")
    if min_success_count is not None and (isinstance(min_success_count, bool) or not isinstance(min_success_count, int) or min_success_count < 0):
        raise ValueError("min_success_count must be non-negative")
    rows = tuple(x for x in reports if min_success_count is None or x.success_count >= min_success_count)
    return LearningReportQueryResult(rows, deterministic_id("learning_report_query",
        {"report_ids": tuple(x.report_id for x in rows), "schema_version": "learning_report_query.v1"}))

@dataclass(frozen=True, slots=True)
class PromotionEvidenceReplayVerification:
    evidence_id: str
    matches: bool
    verification_id: str
    schema_version: str = "promotion_evidence_replay.v1"

def verify_promotion_evidence_replay(evidence: WalkForwardPromotionEvidence,
                                     replayed: WalkForwardPromotionEvidence) -> PromotionEvidenceReplayVerification:
    if not isinstance(evidence, WalkForwardPromotionEvidence) or not isinstance(replayed, WalkForwardPromotionEvidence):
        raise TypeError("evidence values are invalid")
    matches = evidence == replayed
    return PromotionEvidenceReplayVerification(evidence.evidence_id, matches,
        deterministic_id("promotion_evidence_replay", {"evidence_id": evidence.evidence_id,
        "matches": matches, "schema_version": "promotion_evidence_replay.v1"}))

@dataclass(frozen=True, slots=True)
class HumanGatedPatternPromotion:
    proposal_id: str
    reviewer: str
    approved: bool
    rationale: str
    promotion_id: str
    schema_version: str = "human_gated_pattern_promotion.v1"

    def __post_init__(self) -> None:
        if not self.proposal_id.strip() or not self.reviewer.strip() or not self.rationale.strip():
            raise ValueError("promotion fields must be non-empty")
        expected = deterministic_id("human_gated_pattern_promotion", {
            "approved": self.approved, "proposal_id": self.proposal_id,
            "rationale": self.rationale.strip(), "reviewer": self.reviewer.strip(),
            "schema_version": self.schema_version})
        if self.promotion_id != expected:
            raise ValueError("promotion_id mismatch")

def record_human_gated_promotion(proposal_id: str, *, reviewer: str,
                                 approved: bool, rationale: str) -> HumanGatedPatternPromotion:
    if not isinstance(approved, bool):
        raise TypeError("approved must be boolean")
    identity = {"approved": approved, "proposal_id": proposal_id.strip(),
                "rationale": rationale.strip(), "reviewer": reviewer.strip(),
                "schema_version": "human_gated_pattern_promotion.v1"}
    return HumanGatedPatternPromotion(proposal_id, reviewer, approved, rationale,
        deterministic_id("human_gated_pattern_promotion", identity))

__all__ = ["OutcomeReadModel", "build_outcome_read_model", "query_outcomes",
           "LearningReportQueryResult", "query_learning_reports",
           "PromotionEvidenceReplayVerification", "verify_promotion_evidence_replay",
           "HumanGatedPatternPromotion", "record_human_gated_promotion"]
