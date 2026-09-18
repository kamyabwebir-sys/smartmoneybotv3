from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.wallet_behavior_fingerprint import project_wallet_behavior_fingerprint
from smart_money.application.wallet_behavior_fingerprint_ledger import ingest_wallet_behavior_fingerprint
from smart_money.application.wallet_intelligence_profile import WalletIntelligenceProfile
from smart_money.core.ids import deterministic_id


def test_wallet_behavior_fingerprint_projects_to_idempotent_evidence() -> None:
    identity = {
        "activity_count": 2, "buy_count": 1, "data_completeness_bps": 10000,
        "distinct_token_observation_total": 1, "native_delta_total": -1,
        "observed_from_slot": 10, "observed_to_slot": 20, "observation_count": 1,
        "observation_ids": ("obs-1",), "schema_version": "wallet_intelligence_profile.v1",
        "sell_count": 1, "token_delta_total": 3, "unknown_count": 0, "wallet": "W",
    }
    profile = WalletIntelligenceProfile(
        **identity, profile_id=deterministic_id("wallet_intelligence_profile", identity)
    )
    fingerprint = project_wallet_behavior_fingerprint(profile)
    ledger = EvidenceGroundingLedger()
    receipt = ingest_wallet_behavior_fingerprint(fingerprint, ledger)
    payload = ledger.get(receipt.evidence_id)
    assert payload is not None
    assert payload.evidence_type == "wallet_behavior_fingerprint"
    assert payload.data["wallet_behavior_fingerprint"]["fingerprint_id"] == fingerprint.fingerprint_id
    assert payload.metadata["provenance"]["profile_id"] == profile.profile_id
    assert ingest_wallet_behavior_fingerprint(fingerprint, ledger).already_present is True
