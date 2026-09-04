from smart_money.application.token_lifecycle import TokenLifecycleState, build_token_lifecycle
from smart_money.application.token_lifecycle_query import TokenLifecycleQueryResult
from smart_money.application.token_lifecycle_query_audit import audit_token_lifecycle_query
from smart_money.application.token_lifecycle_query_store import TokenLifecycleQueryStore
from smart_money.application.token_lifecycle_outcome_window import bind_outcome_window
from smart_money.core.ids import deterministic_id

def test_query_audit_persistence_and_outcome(tmp_path) -> None:
    qid = deterministic_id("token_lifecycle_query", {"lifecycle_ids": (), "schema_version": "token_lifecycle_query.v1"})
    result = TokenLifecycleQueryResult((), qid)
    receipt = audit_token_lifecycle_query(result, parameters={"token_id": "t"})
    store = TokenLifecycleQueryStore(tmp_path / "q.json")
    store.save(result)
    assert receipt.result_count == 0 and store.get(qid) == result
    lifecycle = build_token_lifecycle("t", TokenLifecycleState.CREATED, 1, ("e1",))
    closed = bind_outcome_window(lifecycle, close_slot=2, evidence_ids=("e1", "e2"))
    assert closed.lifecycle.state is TokenLifecycleState.OUTCOME_WINDOW_CLOSED
