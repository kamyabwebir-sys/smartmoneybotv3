from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.solana_candidate_discovery import SolanaWalletTokenCandidate
from smart_money.application.solana_candidate_ledger_projection import ingest_solana_candidate
from smart_money.application.token_safety_candidate_binding import bind_token_safety_to_candidate
from smart_money.application.token_safety_candidate_binding_ledger import (
    ingest_token_safety_candidate_binding,
)
from smart_money.application.token_safety_candidate_read_model import (
    build_token_safety_candidate_read_model,
)
from smart_money.application.token_safety_candidate_report import (
    build_token_safety_candidate_evidence_report,
)
from smart_money.application.token_safety_parser import parse_token_safety_observation
from smart_money.core.ids import deterministic_id


def test_candidate_evidence_report_is_deterministic():
    identity = {
        "activity_count": 1,
        "buy_count": 1,
        "first_slot": 4,
        "last_slot": 4,
        "mint": "TOKEN",
        "reasons": ("buy_count=1",),
        "schema_version": "solana_wallet_token_candidate.v1",
        "wallet": "W",
    }
    candidate = SolanaWalletTokenCandidate(
        wallet="W", mint="TOKEN", activity_count=1, buy_count=1,
        first_slot=4, last_slot=4, reasons=("buy_count=1",),
        candidate_id=deterministic_id("solana_wallet_token_candidate", identity),
    )
    observation = parse_token_safety_observation({
        "token": "TOKEN", "observed_at": 10, "mint_authority": None,
        "freeze_authority": None, "update_authority": "U",
        "liquidity_amount": 1000, "holder_concentration_bps": 1200,
        "deployer": "D",
    })
    ledger = EvidenceGroundingLedger()
    ingest_solana_candidate(candidate, ledger)
    ingest_token_safety_candidate_binding(
        bind_token_safety_to_candidate(candidate, observation), ledger
    )
    model = build_token_safety_candidate_read_model(ledger)
    report = build_token_safety_candidate_evidence_report(model.rows[0])
    assert report.row.candidate.candidate_id == candidate.candidate_id
    assert report.row.binding.liquidity_amount == 1000
    assert report.report_id
