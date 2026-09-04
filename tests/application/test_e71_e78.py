from smart_money.application.outcome_learning import (
    OutcomeEvidenceProjection,
    build_learning_report,
    evaluate_outcome_window,
    extract_token_outcome,
    verify_outcome_replay,
    walk_forward_evaluate,
)

def test_outcome_learning_pipeline() -> None:
    observation=extract_token_outcome("token",start_slot=1,end_slot=2,start_value=10,end_value=15)
    evaluation=evaluate_outcome_window(observation)
    projection=OutcomeEvidenceProjection.from_evaluation(observation,evaluation)
    assert verify_outcome_replay(observation,evaluation,projection)
    result=walk_forward_evaluate((evaluation,))
    assert build_learning_report(result).success_count==1
