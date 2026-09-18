from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.wallet_behavior_fingerprint import WalletBehaviorFingerprint
from smart_money.application.wallet_cohort_detection import detect_wallet_cohorts
from smart_money.application.wallet_cohort_ledger import ingest_wallet_cohort
from smart_money.core.ids import deterministic_id


def _fingerprint(wallet: str) -> WalletBehaviorFingerprint:
    identity = {
        "activity_per_observation": 3, "buy_ratio_bps": 7000,
        "data_completeness_bps": 10000, "profile_id": f"profile-{wallet}",
        "schema_version": "wallet_behavior_fingerprint.v1", "sell_ratio_bps": 3000,
        "token_observation_ratio_bps": 4000, "unknown_ratio_bps": 0, "wallet": wallet,
    }
    return WalletBehaviorFingerprint(
        **identity, fingerprint_id=deterministic_id("wallet_behavior_fingerprint", identity)
    )


def test_wallet_cohort_projects_with_fingerprint_linkage() -> None:
    cohort = detect_wallet_cohorts((_fingerprint("W1"), _fingerprint("W2")))[0]
    ledger = EvidenceGroundingLedger()
    first = ingest_wallet_cohort(cohort, ledger)
    second = ingest_wallet_cohort(cohort, ledger)
    payload = ledger.get(first.evidence_id)
    assert payload is not None
    assert payload.evidence_type == "wallet_cohort"
    assert tuple(payload.data["wallet_cohort"]["fingerprint_ids"]) == cohort.fingerprint_ids
    assert second.already_present is True
