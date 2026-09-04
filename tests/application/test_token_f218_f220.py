from smart_money.application.token_lifecycle import TokenLifecycleState, build_token_lifecycle
from smart_money.application.token_lifecycle_final_audit import TokenLifecycleFinalAuditReceipt
from smart_money.application.token_lifecycle_final_audit_store import TokenLifecycleFinalAuditStore
from smart_money.application.token_outcome_query import TokenOutcomeQueryResult
from smart_money.application.token_outcome_replay import verify_token_outcome_replay
from smart_money.application.token_candidate_binding import bind_token_candidate
from smart_money.core.ids import deterministic_id

def test_persistence_replay_and_candidate(tmp_path) -> None:
    qid = deterministic_id("token_outcome_query", {"lifecycle_ids": (), "schema_version": "token_outcome_query.v1"})
    result = TokenOutcomeQueryResult((), qid)
    aid = deterministic_id("token_lifecycle_final_audit", {"outcome_count": 0, "query_id": qid, "schema_version": "token_lifecycle_final_audit.v1"})
    receipt = TokenLifecycleFinalAuditReceipt(qid, 0, aid)
    store = TokenLifecycleFinalAuditStore(tmp_path / "audit.json")
    store.save(receipt)
    assert store.get(aid) == receipt
    assert verify_token_outcome_replay(result, result).replay_matches
    lifecycle = build_token_lifecycle("t", TokenLifecycleState.CREATED, 1, ("e",))
    assert bind_token_candidate("t", (lifecycle,)).candidate_id
