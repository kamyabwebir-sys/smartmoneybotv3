from smart_money.application.wallet_candidate_evidence_query import WalletCandidateEvidenceQueryResult
from smart_money.application.wallet_candidate_query_audit import audit_wallet_candidate_query
from smart_money.core.ids import deterministic_id


def test_wallet_candidate_query_audit_is_deterministic() -> None:
    query_id = deterministic_id(
        "wallet_candidate_evidence_query",
        {"evidence_ids": (), "schema_version": "wallet_candidate_evidence_query.v1"},
    )
    result = WalletCandidateEvidenceQueryResult(rows=(), query_id=query_id)
    receipt = audit_wallet_candidate_query(result, parameters={"wallet": "wallet-a"})
    assert receipt.result_count == 0
    assert receipt.query_id == query_id
    assert receipt.audit_id == audit_wallet_candidate_query(
        result, parameters={"wallet": "wallet-a"}
    ).audit_id
