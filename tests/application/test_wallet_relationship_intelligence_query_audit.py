from smart_money.application.wallet_relationship_intelligence_query import (
    WalletRelationshipIntelligenceQueryResult,
)
from smart_money.application.wallet_relationship_intelligence_query_audit import (
    audit_wallet_relationship_intelligence_query,
)
from smart_money.core.ids import deterministic_id


def test_wallet_relationship_intelligence_query_audit_receipt() -> None:
    identity = {
        "intelligence_ids": (),
        "schema_version": "wallet_relationship_intelligence_query.v1",
    }
    result = WalletRelationshipIntelligenceQueryResult(
        rows=(),
        query_id=deterministic_id("wallet_relationship_intelligence_query", identity),
    )
    audit = audit_wallet_relationship_intelligence_query(
        result, parameters={"wallet": "wallet-a", "min_relationship_count": "2"}
    )
    assert audit.query_id == result.query_id
    assert audit.result_count == 0
    assert audit.audit_id
