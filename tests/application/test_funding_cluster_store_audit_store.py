from smart_money.adapters.persistence.funding_cluster_store_audit_store import (
    JsonFundingClusterStoreAuditStore,
)
from smart_money.application.funding_cluster_store_audit import (
    FundingClusterStoreAuditReceipt,
)
from smart_money.core.ids import deterministic_id


def test_funding_cluster_store_audit_store_round_trip_and_idempotency(tmp_path) -> None:
    identity = {
        "cluster_id": "cluster-1",
        "ledger_receipt_id": "ledger-1",
        "replay_id": "replay-1",
        "replay_matches": True,
        "schema_version": "funding_cluster_store_audit.v1",
        "store_replay_id": "store-replay-1",
    }
    receipt = FundingClusterStoreAuditReceipt(
        **identity,
        audit_id=deterministic_id("funding_cluster_store_audit", identity),
    )
    path = tmp_path / "audit.json"
    store = JsonFundingClusterStoreAuditStore(path)
    assert store.append(receipt) == receipt.audit_id
    assert store.append(receipt) == receipt.audit_id
    restored = JsonFundingClusterStoreAuditStore(path)
    assert restored.get(receipt.audit_id) == receipt
    assert restored.receipt_count == 1
