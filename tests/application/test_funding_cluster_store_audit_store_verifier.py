from smart_money.adapters.persistence.funding_cluster_store_audit_store import (
    JsonFundingClusterStoreAuditStore,
)
from smart_money.application.funding_cluster_store_audit import (
    FundingClusterStoreAuditReceipt,
)
from smart_money.application.funding_cluster_store_audit_store_verifier import (
    verify_funding_cluster_store_audit_store,
)
from smart_money.core.ids import deterministic_id


def test_funding_cluster_store_audit_store_replay_verification(tmp_path) -> None:
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
    store = JsonFundingClusterStoreAuditStore(tmp_path / "audit.json")
    store.append(receipt)
    verification = verify_funding_cluster_store_audit_store(store, receipt)
    assert verification.matches is True
    assert verification.audit_id == receipt.audit_id
