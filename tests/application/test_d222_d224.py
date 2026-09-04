from smart_money.application.token_safety_candidate_query import TokenSafetyCandidateQueryResult
from smart_money.application.token_safety_candidate_query_audit import audit_token_safety_candidate_query
from smart_money.application.token_safety_candidate_query_store import TokenSafetyCandidateQueryStore
from smart_money.core.ids import deterministic_id

def test_candidate_query_audit_and_persistence(tmp_path) -> None:
    query_id = deterministic_id("token_safety_candidate_query", {"binding_ids": (), "schema_version": "token_safety_candidate_query.v1"})
    result = TokenSafetyCandidateQueryResult((), query_id)
    receipt = audit_token_safety_candidate_query(result, parameters={"token": "t"})
    store = TokenSafetyCandidateQueryStore(tmp_path / "query.json")
    store.save(result)
    assert receipt.result_count == 0
    assert store.get(query_id) == result
