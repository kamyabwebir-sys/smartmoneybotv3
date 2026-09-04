from smart_money.adapters.persistence.funding_cluster_audit_chain_final_store import (
    JsonFundingClusterAuditChainFinalStore,
)
from smart_money.application.funding_cluster_audit_chain_final import (
    FundingClusterAuditChainFinalReceipt,
)
from smart_money.core.ids import deterministic_id


def test_funding_cluster_audit_final_store_round_trip_and_idempotency(tmp_path) -> None:
    identity = {
        "accepted": True,
        "chain_id": "chain-1",
        "cluster_id": "cluster-1",
        "gate_id": "gate-1",
        "schema_version": "funding_cluster_audit_chain_final.v1",
        "store_verification_id": "verification-1",
    }
    receipt = FundingClusterAuditChainFinalReceipt(
        **identity,
        final_id=deterministic_id("funding_cluster_audit_chain_final", identity),
    )
    path = tmp_path / "final.json"
    store = JsonFundingClusterAuditChainFinalStore(path)
    assert store.append(receipt) == receipt.final_id
    assert store.append(receipt) == receipt.final_id
    restored = JsonFundingClusterAuditChainFinalStore(path)
    assert restored.get(receipt.final_id) == receipt
    assert restored.receipt_count == 1
