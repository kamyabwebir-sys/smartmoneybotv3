from smart_money.application.wallet_cohort_audit import build_wallet_cohort_audit_receipt
from smart_money.application.wallet_cohort_ledger import WalletCohortLedgerReceipt
from smart_money.application.wallet_cohort_replay import WalletCohortReplayReceipt
from smart_money.application.wallet_cohort_replay_store_verifier import (
    WalletCohortReplayStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id


def test_wallet_cohort_audit_binds_detection_projection_replay_and_store() -> None:
    ledger_identity = {
        "already_present": False,
        "cohort_id": "cohort-1",
        "evidence_id": "evidence-1",
        "ledger_entry_count": 1,
        "schema_version": "wallet_cohort_ledger.v1",
    }
    ledger_receipt = WalletCohortLedgerReceipt(
        **ledger_identity,
        receipt_id=deterministic_id("wallet_cohort_ledger", ledger_identity),
    )
    replay_identity = {
        "cohort_id": "cohort-1",
        "matches": True,
        "schema_version": "wallet_cohort_replay.v1",
    }
    replay = WalletCohortReplayReceipt(
        **replay_identity,
        replay_id=deterministic_id("wallet_cohort_replay", replay_identity),
    )
    verification_identity = {
        "matches": True,
        "replay_id": replay.replay_id,
        "schema_version": "wallet_cohort_replay_store_verifier.v1",
    }
    verification = WalletCohortReplayStoreVerificationReceipt(
        **verification_identity,
        verification_id=deterministic_id(
            "wallet_cohort_replay_store_verification", verification_identity
        ),
    )
    receipt = build_wallet_cohort_audit_receipt(
        cohort_id="cohort-1",
        ledger_receipt=ledger_receipt,
        replay_receipt=replay,
        store_verification=verification,
    )
    assert receipt.replay_matches is True
    assert receipt.audit_id
