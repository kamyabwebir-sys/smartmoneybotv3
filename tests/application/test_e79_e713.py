from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.outcome_governance import (
    LearningReportStore, OutcomeStore, build_walk_forward_promotion_evidence,
    ingest_outcome, verify_outcome_store,
)
from smart_money.application.outcome_learning import build_learning_report, extract_token_outcome, evaluate_outcome_window, walk_forward_evaluate

def test_outcome_governance(tmp_path) -> None:
    observation=extract_token_outcome("t",start_slot=1,end_slot=2,start_value=1,end_value=2)
    ledger=EvidenceGroundingLedger()
    assert ingest_outcome(observation,ledger).evidence_id
    store=OutcomeStore(tmp_path/"outcomes.json")
    store.save(observation)
    assert verify_outcome_store(observation,store).matches
    report=build_learning_report(walk_forward_evaluate((evaluate_outcome_window(observation),)))
    report_store=LearningReportStore(tmp_path/"reports.json")
    report_store.save(report)
    assert report_store.get(report.report_id)==report
    assert build_walk_forward_promotion_evidence(report).evidence_id
