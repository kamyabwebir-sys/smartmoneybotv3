from smart_money.application.funding_cluster_audit import build_funding_cluster_audit_receipt
from smart_money.application.funding_cluster_ledger import FundingClusterLedgerReceipt
from smart_money.application.funding_cluster_replay import FundingClusterReplayReceipt
from smart_money.application.funding_cluster_replay_store_verifier import (
    FundingClusterReplayStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id


def test_funding_cluster_audit_binds_full_chain() -> None:
    ledger_identity = {
        "already_present": False,
        "cluster_id": "cluster-1",
        "evidence_id": "e-1",
        "ledger_entry_count": 1,
        "schema_version": "funding_cluster_ledger.v1",
    }
    ledger = FundingClusterLedgerReceipt(
        **ledger_identity,
        receipt_id=deterministic_id("funding_cluster_ledger", ledger_identity),
    )
    replay_identity = {
        "cluster_id": "cluster-1",
        "matches": True,
        "schema_version": "funding_cluster_replay.v1",
    }
    replay = FundingClusterReplayReceipt(
        **replay_identity,
        replay_id=deterministic_id("funding_cluster_replay", replay_identity),
    )
    verification_identity = {
        "matches": True,
        "replay_id": replay.replay_id,
        "schema_version": "funding_cluster_replay_store_verifier.v1",
    }
    verification = FundingClusterReplayStoreVerificationReceipt(
        **verification_identity,
        verification_id=deterministic_id(
            "funding_cluster_replay_store_verification", verification_identity
        ),
    )
    receipt = build_funding_cluster_audit_receipt(
        cluster_id=" cluster-1 ",
        ledger_receipt=ledger,
        replay_receipt=replay,
        store_verification=verification,
    )
    assert receipt.replay_matches is True
    assert receipt.audit_id
