from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from smart_money.application.outcome_learning import OutcomeObservation, LearningReport
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload

@dataclass(frozen=True, slots=True)
class OutcomeLedgerReceipt:
    outcome_id: str
    evidence_id: str
    already_present: bool

def ingest_outcome(observation: OutcomeObservation, ledger: EvidenceLedger) -> OutcomeLedgerReceipt:
    if not isinstance(observation, OutcomeObservation) or not isinstance(ledger, EvidenceLedger):
        raise TypeError("invalid observation or ledger")
    payload = EvidencePayload(source_id="outcome-learning", evidence_type="outcome_observation",
                              timestamp=observation.end_slot, data={"outcome": observation.canonical_dict()},
                              metadata={"authority":"NONE","classification":"EVIDENCE",
                                        "verification_status":"UNKNOWN",
                                        "provenance":{"outcome_id":observation.outcome_id}})
    evidence_id = payload.get_canonical_id()
    present = ledger.contains(evidence_id)
    if ledger.append(payload) != evidence_id:
        raise ValueError("ledger identity mismatch")
    return OutcomeLedgerReceipt(observation.outcome_id, evidence_id, present)

class OutcomeStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._items: dict[str, OutcomeObservation] = {}
    def save(self, observation: OutcomeObservation) -> str:
        if not isinstance(observation, OutcomeObservation):
            raise TypeError("observation must be OutcomeObservation")
        self._items[observation.outcome_id] = observation
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"schema_version":"outcome_store.v1",
            "items":[x.canonical_dict() for x in self._items.values()]},
            sort_keys=True, separators=(",",":")), encoding="utf-8")
        return observation.outcome_id
    def get(self, outcome_id: str) -> OutcomeObservation | None:
        return self._items.get(outcome_id)

@dataclass(frozen=True, slots=True)
class OutcomeStoreReplayVerification:
    outcome_id: str
    matches: bool
    verification_id: str
    schema_version: str = "outcome_store_replay.v1"

def verify_outcome_store(observation: OutcomeObservation, store: OutcomeStore) -> OutcomeStoreReplayVerification:
    matches = store.get(observation.outcome_id) == observation
    identity={"outcome_id":observation.outcome_id,"matches":matches,"schema_version":"outcome_store_replay.v1"}
    return OutcomeStoreReplayVerification(observation.outcome_id,matches,
        deterministic_id("outcome_store_replay",identity))

class LearningReportStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._items: dict[str, LearningReport] = {}
    def save(self, report: LearningReport) -> str:
        if not isinstance(report, LearningReport):
            raise TypeError("report must be LearningReport")
        self._items[report.report_id]=report
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.path.write_text(json.dumps({"schema_version":"learning_report_store.v1","items":[x.canonical_dict() for x in self._items.values()]},sort_keys=True,separators=(",",":")),encoding="utf-8")
        return report.report_id
    def get(self, report_id: str) -> LearningReport | None: return self._items.get(report_id)

@dataclass(frozen=True, slots=True)
class WalkForwardPromotionEvidence:
    report_id: str
    sample_count: int
    success_count: int
    evidence_id: str
    schema_version: str = "walk_forward_promotion_evidence.v1"
    def __post_init__(self) -> None:
        if self.evidence_id != deterministic_id("walk_forward_promotion_evidence", self.identity_payload()):
            raise ValueError("evidence_id mismatch")
    def identity_payload(self) -> dict[str, object]:
        return {"report_id":self.report_id,"sample_count":self.sample_count,"success_count":self.success_count,"schema_version":self.schema_version}

def build_walk_forward_promotion_evidence(report: LearningReport) -> WalkForwardPromotionEvidence:
    identity={"report_id":report.report_id,"sample_count":report.sample_count,"success_count":report.success_count,"schema_version":"walk_forward_promotion_evidence.v1"}
    return WalkForwardPromotionEvidence(report.report_id,report.sample_count,report.success_count,
        deterministic_id("walk_forward_promotion_evidence",identity))

__all__=["OutcomeLedgerReceipt","ingest_outcome","OutcomeStore","OutcomeStoreReplayVerification","verify_outcome_store","LearningReportStore","WalkForwardPromotionEvidence","build_walk_forward_promotion_evidence"]
