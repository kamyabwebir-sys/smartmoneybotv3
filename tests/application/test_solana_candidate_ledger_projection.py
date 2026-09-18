from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.solana_candidate_ledger_projection import ingest_solana_candidate
from smart_money.application.solana_candidate_discovery import (
    SolanaWalletTokenCandidate,
)
from smart_money.core.ids import deterministic_id


def test_candidate_projection_is_idempotent():
    schema = "solana_wallet_token_candidate.v1"
    identity = {
        "activity_count": 1, "buy_count": 1, "first_slot": 4, "last_slot": 4,
        "mint": "M", "reasons": ("buy_count=1",), "schema_version": schema,
        "wallet": "W",
    }
    candidate = SolanaWalletTokenCandidate(
        wallet="W", mint="M", activity_count=1, buy_count=1,
        first_slot=4, last_slot=4, reasons=("buy_count=1",),
        candidate_id=deterministic_id("solana_wallet_token_candidate", identity),
    )
    ledger = EvidenceGroundingLedger()
    first = ingest_solana_candidate(candidate, ledger)
    second = ingest_solana_candidate(candidate, ledger)
    assert first.evidence_id == second.evidence_id
    assert second.already_present is True
    assert ledger.entry_count == 1
