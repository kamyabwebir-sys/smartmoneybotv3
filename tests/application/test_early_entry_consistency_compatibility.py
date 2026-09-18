from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.early_entry_consistency import evaluate_early_entry_consistency
from smart_money.application.early_entry_consistency_compatibility import (
    replay_early_entry_consistency_compatibility,
)
from smart_money.application.early_entry_consistency_ledger import ingest_early_entry_consistency
from smart_money.application.solana_wallet_token_activity import SolanaWalletTokenActivityEvidence
from smart_money.core.ids import deterministic_id


def _activity(slot: int, mint: str, signature: str) -> SolanaWalletTokenActivityEvidence:
    identity = {
        "direction": "BUY", "mint": mint, "native_delta": -1,
        "schema_version": "solana_wallet_token_activity.v1", "slot": slot,
        "token_delta": 10, "transaction_signature": signature, "wallet": "W",
    }
    return SolanaWalletTokenActivityEvidence(
        **identity, activity_id=deterministic_id("solana_wallet_token_activity", identity)
    )


def test_compatibility_replays_new_and_legacy_payloads() -> None:
    value = evaluate_early_entry_consistency(
        (_activity(10, "T1", "S1"), _activity(30, "T2", "S2")),
        reference_slots={"T1": 20, "T2": 20},
    )
    ledger = EvidenceGroundingLedger()
    ingest_early_entry_consistency(value, ledger)
    replayed = replay_early_entry_consistency_compatibility(ledger)
    assert replayed == (value,)

    legacy = dict(value.canonical_dict())
    legacy.pop("observed_from_slot")
    legacy.pop("observed_to_slot")
    legacy["consistency_id"] = deterministic_id(
        "early_entry_consistency",
        {key: legacy[key] for key in legacy if key != "consistency_id"},
    )
    legacy_ledger = EvidenceGroundingLedger()
    from smart_money.ingestion.contracts import EvidencePayload
    legacy_ledger.append(
        EvidencePayload(
            source_id="wallet_intelligence",
            evidence_type="early_entry_consistency",
            timestamp=0,
            data={"early_entry_consistency": legacy},
            metadata={"authority": "NONE", "classification": "EVIDENCE"},
        )
    )
    assert replay_early_entry_consistency_compatibility(legacy_ledger)[0].observed_from_slot is None
