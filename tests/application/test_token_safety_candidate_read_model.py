from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.solana_candidate_discovery import SolanaWalletTokenCandidate
from smart_money.application.solana_candidate_ledger_projection import ingest_solana_candidate
from smart_money.application.token_safety_candidate_binding import bind_token_safety_to_candidate
from smart_money.application.token_safety_candidate_binding_ledger import ingest_token_safety_candidate_binding
from smart_money.application.token_safety_parser import parse_token_safety_observation
from smart_money.application.token_safety_candidate_read_model import build_token_safety_candidate_read_model
from smart_money.core.ids import deterministic_id


def test_integrated_read_model_binds_candidate_and_safety():
    ident = {"activity_count": 1, "buy_count": 1, "first_slot": 4, "last_slot": 4, "mint": "TOKEN", "reasons": ("buy_count=1",), "schema_version": "solana_wallet_token_candidate.v1", "wallet": "W"}
    candidate = SolanaWalletTokenCandidate("W", "TOKEN", 1, 1, 4, 4, ("buy_count=1",), deterministic_id("solana_wallet_token_candidate", ident))
    observation = parse_token_safety_observation({"token": "TOKEN", "observed_at": 10, "mint_authority": None, "freeze_authority": None, "update_authority": "U", "liquidity_amount": 100, "holder_concentration_bps": 1000, "deployer": "D"})
    ledger = EvidenceGroundingLedger()
    ingest_solana_candidate(candidate, ledger)
    ingest_token_safety_candidate_binding(bind_token_safety_to_candidate(candidate, observation), ledger)
    model = build_token_safety_candidate_read_model(ledger)
    assert len(model.rows) == 1
    assert model.rows[0].candidate.mint == "TOKEN"
    assert model.rows[0].replay_verified is True
