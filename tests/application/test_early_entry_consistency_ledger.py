from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.early_entry_consistency import evaluate_early_entry_consistency
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


def test_early_entry_consistency_projects_idempotently() -> None:
    consistency = evaluate_early_entry_consistency(
        (_activity(10, "T1", "S1"), _activity(30, "T2", "S2")),
        reference_slots={"T1": 20, "T2": 20},
    )
    ledger = EvidenceGroundingLedger()
    first = ingest_early_entry_consistency(consistency, ledger)
    second = ingest_early_entry_consistency(consistency, ledger)
    payload = ledger.get(first.evidence_id)
    assert payload is not None
    assert payload.evidence_type == "early_entry_consistency"
    assert payload.data["early_entry_consistency"]["consistency_bps"] == 5000
    assert second.already_present is True
