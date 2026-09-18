from smart_money.adapters.persistence.funding_cluster_audit_chain_store import (
    JsonFundingClusterAuditChainStore,
)
from smart_money.application.funding_cluster_audit_chain import (
    FundingClusterAuditChainReceipt,
)
from smart_money.core.ids import deterministic_id


def test_funding_cluster_audit_chain_store_round_trip_and_idempotency(tmp_path) -> None:
    identity = {
        "audit_id": "audit-1",
        "chain_matches": True,
        "cluster_id": "cluster-1",
        "schema_version": "funding_cluster_audit_chain.v1",
        "verification_id": "verification-1",
    }
    receipt = FundingClusterAuditChainReceipt(
        **identity,
        chain_id=deterministic_id("funding_cluster_audit_chain", identity),
    )
    path = tmp_path / "chain.json"
    store = JsonFundingClusterAuditChainStore(path)
    assert store.append(receipt) == receipt.chain_id
    assert store.append(receipt) == receipt.chain_id
    restored = JsonFundingClusterAuditChainStore(path)
    assert restored.get(receipt.chain_id) == receipt
    assert restored.receipt_count == 1
