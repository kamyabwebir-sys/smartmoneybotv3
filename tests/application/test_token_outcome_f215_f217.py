from smart_money.application.token_lifecycle import TokenLifecycleState, build_token_lifecycle
from smart_money.application.token_lifecycle_outcome_window import TokenLifecycleOutcomeWindow
from smart_money.application.token_outcome_read_model import build_token_outcome_window_read_model
from smart_money.application.token_outcome_query import query_token_outcome_windows
from smart_money.application.token_lifecycle_final_audit import build_token_lifecycle_final_audit

def test_outcome_read_query_and_final_audit() -> None:
    lifecycle = build_token_lifecycle("t", TokenLifecycleState.OUTCOME_WINDOW_CLOSED, 1, ("e1",))
    window = TokenLifecycleOutcomeWindow(lifecycle, 5)
    result = query_token_outcome_windows(build_token_outcome_window_read_model((window,)), token_id=" t ")
    receipt = build_token_lifecycle_final_audit(result)
    assert len(result.rows) == 1
    assert receipt.outcome_count == 1
    assert receipt.audit_id
