from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload

@dataclass(frozen=True, slots=True)
class OutcomeObservation:
    subject_id: str
    subject_kind: str
    start_slot: int
    end_slot: int
    start_value: int
    end_value: int
    outcome_id: str
    schema_version: str = "outcome_observation.v1"
    def __post_init__(self) -> None:
        if not self.subject_id.strip() or self.subject_kind not in {"wallet","token"}:
            raise ValueError("invalid subject")
        if self.end_slot < self.start_slot or self.start_value < 0 or self.end_value < 0:
            raise ValueError("invalid outcome window")
        if self.outcome_id != deterministic_id("outcome_observation", self.identity_payload()):
            raise ValueError("outcome_id mismatch")
    def identity_payload(self)->dict[str,Any]:
        return {"end_slot":self.end_slot,"end_value":self.end_value,"schema_version":self.schema_version,"start_slot":self.start_slot,"start_value":self.start_value,"subject_id":self.subject_id.strip(),"subject_kind":self.subject_kind}
    def canonical_dict(self)->dict[str,Any]: return {"outcome_id":self.outcome_id,**self.identity_payload()}

def extract_wallet_outcome(wallet_id: str, *, start_slot:int, end_slot:int, start_value:int, end_value:int)->OutcomeObservation:
    identity={"end_slot":end_slot,"end_value":end_value,"schema_version":"outcome_observation.v1","start_slot":start_slot,"start_value":start_value,"subject_id":wallet_id.strip(),"subject_kind":"wallet"}
    return OutcomeObservation(wallet_id,"wallet",start_slot,end_slot,start_value,end_value,deterministic_id("outcome_observation",identity))

def extract_token_outcome(token_id: str, *, start_slot:int, end_slot:int, start_value:int, end_value:int)->OutcomeObservation:
    identity={"end_slot":end_slot,"end_value":end_value,"schema_version":"outcome_observation.v1","start_slot":start_slot,"start_value":start_value,"subject_id":token_id.strip(),"subject_kind":"token"}
    return OutcomeObservation(token_id,"token",start_slot,end_slot,start_value,end_value,deterministic_id("outcome_observation",identity))

@dataclass(frozen=True, slots=True)
class OutcomeWindowEvaluation:
    outcome_id: str
    delta: int
    improved: bool
    evaluation_id: str
    schema_version: str = "outcome_window_evaluation.v1"

def evaluate_outcome_window(observation: OutcomeObservation)->OutcomeWindowEvaluation:
    delta=observation.end_value-observation.start_value
    identity={"delta":delta,"improved":delta>0,"outcome_id":observation.outcome_id,"schema_version":"outcome_window_evaluation.v1"}
    return OutcomeWindowEvaluation(observation.outcome_id,delta,delta>0,deterministic_id("outcome_window_evaluation",identity))

@dataclass(frozen=True, slots=True)
class OutcomeEvidenceProjection:
    payload: EvidencePayload
    outcome_id: str
    @classmethod
    def from_evaluation(cls, observation: OutcomeObservation, evaluation: OutcomeWindowEvaluation)->"OutcomeEvidenceProjection":
        payload=EvidencePayload(source_id="outcome-learning",evidence_type="outcome_evidence",timestamp=observation.end_slot,data={"observation":observation.canonical_dict(),"evaluation":{"outcome_id":evaluation.outcome_id,"delta":evaluation.delta,"improved":evaluation.improved,"evaluation_id":evaluation.evaluation_id}},metadata={"authority":"NONE","classification":"EVIDENCE","verification_status":"UNKNOWN","provenance":{"outcome_id":observation.outcome_id}})
        return cls(payload,observation.outcome_id)

def verify_outcome_replay(observation: OutcomeObservation, evaluation: OutcomeWindowEvaluation, projection: OutcomeEvidenceProjection)->bool:
    return OutcomeEvidenceProjection.from_evaluation(observation,evaluation).payload.get_canonical_id()==projection.payload.get_canonical_id()

@dataclass(frozen=True, slots=True)
class WalkForwardResult:
    evaluation_ids: tuple[str,...]
    success_count: int
    sample_count: int
    report_id: str

def walk_forward_evaluate(evaluations: tuple[OutcomeWindowEvaluation,...])->WalkForwardResult:
    success=sum(item.improved for item in evaluations)
    identity={"evaluation_ids":tuple(item.evaluation_id for item in evaluations),"sample_count":len(evaluations),"success_count":success}
    return WalkForwardResult(identity["evaluation_ids"],success,len(evaluations),deterministic_id("walk_forward_result",identity))

@dataclass(frozen=True, slots=True)
class LearningReport:
    report_id: str
    sample_count: int
    success_count: int
    schema_version: str = "learning_report.v1"
    def canonical_dict(self)->dict[str,Any]: return {"report_id":self.report_id,"sample_count":self.sample_count,"schema_version":self.schema_version,"success_count":self.success_count}

def build_learning_report(result: WalkForwardResult)->LearningReport:
    return LearningReport(result.report_id,result.sample_count,result.success_count)

__all__=["OutcomeObservation","extract_wallet_outcome","extract_token_outcome","OutcomeWindowEvaluation","evaluate_outcome_window","OutcomeEvidenceProjection","verify_outcome_replay","WalkForwardResult","walk_forward_evaluate","LearningReport","build_learning_report"]
