from smart_money.application.outcome_learning import extract_token_outcome, LearningReport
from smart_money.application.outcome_governance import build_walk_forward_promotion_evidence
from smart_money.application.outcome_queries_promotion import (
    build_outcome_read_model, query_outcomes, query_learning_reports,
    verify_promotion_evidence_replay, record_human_gated_promotion,
)

def test_outcome_queries_and_human_gate() -> None:
    outcome = extract_token_outcome("t", start_slot=1, end_slot=2, start_value=1, end_value=2)
    assert len(query_outcomes(build_outcome_read_model((outcome,)), subject_kind="token")) == 1
    report = LearningReport("report", 1, 1)
    assert len(query_learning_reports((report,), min_success_count=1).rows) == 1
    evidence = build_walk_forward_promotion_evidence(report)
    assert verify_promotion_evidence_replay(evidence, evidence).matches
    assert record_human_gated_promotion("proposal", reviewer="human", approved=True, rationale="approved").approved
