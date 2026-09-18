from smart_money.adapters.persistence.funding_cluster_audit_chain_store import (
    JsonFundingClusterAuditChainStore,
)
from smart_money.application.funding_cluster_audit_chain import FundingClusterAuditChainReceipt
from smart_money.application.funding_cluster_audit_chain_store_verifier import (
    verify_funding_cluster_audit_chain_store,
)
from smart_money.core.ids import deterministic_id


def test_funding_cluster_audit_chain_store_replay_verification(tmp_path) -> None:
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
    store = JsonFundingClusterAuditChainStore(tmp_path / "chain.json")
    store.append(receipt)
    verification = verify_funding_cluster_audit_chain_store(store, receipt)
    assert verification.matches is True
    assert verification.chain_id == receipt.chain_id
