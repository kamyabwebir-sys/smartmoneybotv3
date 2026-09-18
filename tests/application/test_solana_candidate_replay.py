import pytest

from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.solana_candidate_discovery import SolanaWalletTokenCandidate
from smart_money.application.solana_candidate_ledger_projection import ingest_solana_candidate
from smart_money.application.solana_candidate_replay import replay_verify_solana_candidate
from smart_money.core.ids import deterministic_id


def _candidate() -> SolanaWalletTokenCandidate:
    schema = "solana_wallet_token_candidate.v1"
    identity = {
        "activity_count": 1, "buy_count": 1, "first_slot": 4, "last_slot": 4,
        "mint": "M", "reasons": ("buy_count=1",), "schema_version": schema, "wallet": "W",
    }
    return SolanaWalletTokenCandidate(
        wallet="W", mint="M", activity_count=1, buy_count=1, first_slot=4, last_slot=4,
        reasons=("buy_count=1",),
        candidate_id=deterministic_id("solana_wallet_token_candidate", identity),
    )


def test_candidate_replay_matches_ledger_evidence():
    candidate = _candidate()
    ledger = EvidenceGroundingLedger()
    ingest_solana_candidate(candidate, ledger)
    receipt = replay_verify_solana_candidate(candidate, ledger)
    assert receipt.matches is True
    assert receipt.candidate_id == candidate.candidate_id


def test_candidate_replay_fails_when_missing():
    with pytest.raises(ValueError, match="missing"):
        replay_verify_solana_candidate(_candidate(), EvidenceGroundingLedger())
