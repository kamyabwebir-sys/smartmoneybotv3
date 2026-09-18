from smart_money.adapters.persistence.funding_cluster_audit_chain_store import (
    JsonFundingClusterAuditChainStore,
)
from smart_money.application.funding_cluster_audit_chain import FundingClusterAuditChainReceipt
from smart_money.application.funding_cluster_audit_chain_recovery_gate import (
    evaluate_funding_cluster_audit_chain_recovery_gate,
)
from smart_money.core.ids import deterministic_id


def _receipt() -> FundingClusterAuditChainReceipt:
    identity = {
        "audit_id": "audit-1",
        "chain_matches": True,
        "cluster_id": "cluster-1",
        "schema_version": "funding_cluster_audit_chain.v1",
        "verification_id": "verification-1",
    }
    return FundingClusterAuditChainReceipt(
        **identity,
        chain_id=deterministic_id("funding_cluster_audit_chain", identity),
    )


def test_recovery_gate_allows_verified_chain(tmp_path) -> None:
    receipt = _receipt()
    store = JsonFundingClusterAuditChainStore(tmp_path / "chain.json")
    store.append(receipt)
    gate = evaluate_funding_cluster_audit_chain_recovery_gate(store, receipt)
    assert gate.allowed is True
    assert gate.reason == "verified"


def test_recovery_gate_blocks_missing_chain(tmp_path) -> None:
    receipt = _receipt()
    store = JsonFundingClusterAuditChainStore(tmp_path / "chain.json")
    gate = evaluate_funding_cluster_audit_chain_recovery_gate(store, receipt)
    assert gate.allowed is False
    assert gate.reason.startswith("recovery_blocked:")
