from smart_money.adapters.persistence.funding_cluster_audit_chain_final_store import (
    JsonFundingClusterAuditChainFinalStore,
)
from smart_money.application.funding_cluster_audit_chain_e2e_replay import (
    replay_funding_cluster_audit_chain_end_to_end,
)
from smart_money.application.funding_cluster_audit_chain_final import (
    FundingClusterAuditChainFinalReceipt,
)
from smart_money.core.ids import deterministic_id


def test_funding_cluster_audit_chain_end_to_end_replay(tmp_path) -> None:
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
    store = JsonFundingClusterAuditChainFinalStore(tmp_path / "final.json")
    store.append(receipt)
    replay = replay_funding_cluster_audit_chain_end_to_end(store, receipt)
    assert replay.matches is True
    assert replay.final_id == receipt.final_id
