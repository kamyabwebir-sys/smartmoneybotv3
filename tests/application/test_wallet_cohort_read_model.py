from smart_money.application.wallet_behavior_fingerprint import WalletBehaviorFingerprint
from smart_money.application.wallet_cohort_audit import build_wallet_cohort_audit_receipt
from smart_money.application.wallet_cohort_detection import detect_wallet_cohorts
from smart_money.application.wallet_cohort_ledger import WalletCohortLedgerReceipt
from smart_money.application.wallet_cohort_read_model import build_wallet_cohort_read_model
from smart_money.application.wallet_cohort_replay import WalletCohortReplayReceipt
from smart_money.application.wallet_cohort_replay_store_verifier import WalletCohortReplayStoreVerificationReceipt
from smart_money.core.ids import deterministic_id


def _fingerprint(wallet: str) -> WalletBehaviorFingerprint:
    identity = {"activity_per_observation": 3, "buy_ratio_bps": 7000, "data_completeness_bps": 10000, "profile_id": f"profile-{wallet}", "schema_version": "wallet_behavior_fingerprint.v1", "sell_ratio_bps": 3000, "token_observation_ratio_bps": 4000, "unknown_ratio_bps": 0, "wallet": wallet}
    return WalletBehaviorFingerprint(**identity, fingerprint_id=deterministic_id("wallet_behavior_fingerprint", identity))


def test_wallet_cohort_read_model_binds_all_evidence() -> None:
    fingerprints = (_fingerprint("W1"), _fingerprint("W2"))
    cohort = detect_wallet_cohorts(fingerprints)[0]
    replay_identity = {"cohort_id": cohort.cohort_id, "matches": True, "schema_version": "wallet_cohort_replay.v1"}
    replay = WalletCohortReplayReceipt(**replay_identity, replay_id=deterministic_id("wallet_cohort_replay", replay_identity))
    verification_identity = {"matches": True, "replay_id": replay.replay_id, "schema_version": "wallet_cohort_replay_store_verifier.v1"}
    verification = WalletCohortReplayStoreVerificationReceipt(**verification_identity, verification_id=deterministic_id("wallet_cohort_replay_store_verification", verification_identity))
    ledger_identity = {"already_present": False, "cohort_id": cohort.cohort_id, "evidence_id": "e", "ledger_entry_count": 1, "schema_version": "wallet_cohort_ledger.v1"}
    ledger = WalletCohortLedgerReceipt(**ledger_identity, receipt_id=deterministic_id("wallet_cohort_ledger", ledger_identity))
    audit = build_wallet_cohort_audit_receipt(cohort_id=cohort.cohort_id, ledger_receipt=ledger, replay_receipt=replay, store_verification=verification)
    model = build_wallet_cohort_read_model((cohort,), fingerprints, (replay,), (audit,))
    assert len(model.rows) == 1
    assert model.rows[0].audit_receipt.replay_matches is True
    assert model.model_id
