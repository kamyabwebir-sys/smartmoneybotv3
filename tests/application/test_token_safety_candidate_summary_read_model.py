from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.solana_candidate_discovery import SolanaWalletTokenCandidate
from smart_money.application.token_safety_candidate_binding import bind_token_safety_to_candidate
from smart_money.application.token_safety_candidate_summary_binding import bind_candidate_safety_summary
from smart_money.application.token_safety_candidate_summary_ledger import ingest_token_safety_candidate_summary_binding
from smart_money.application.token_safety_candidate_summary_read_model import build_token_safety_candidate_summary_read_model
from smart_money.application.token_safety_evidence_summary import summarize_token_safety_evidence
from smart_money.application.token_safety_parser import parse_token_safety_observation
from smart_money.application.token_safety_rule_evaluation import evaluate_token_safety_rules
from smart_money.core.ids import deterministic_id


def test_candidate_summary_read_model_reconstructs_and_replays():
    identity = {"activity_count": 1, "buy_count": 1, "first_slot": 4, "last_slot": 4, "mint": "TOKEN", "reasons": ("buy_count=1",), "schema_version": "solana_wallet_token_candidate.v1", "wallet": "W"}
    candidate = SolanaWalletTokenCandidate("W", "TOKEN", 1, 1, 4, 4, ("buy_count=1",), deterministic_id("solana_wallet_token_candidate", identity))
    observation = parse_token_safety_observation({"token": "TOKEN", "observed_at": 10, "mint_authority": None, "freeze_authority": None, "update_authority": "U", "liquidity_amount": 1000, "holder_concentration_bps": 1200, "deployer": "D"})
    summary = summarize_token_safety_evidence(evaluate_token_safety_rules(observation))
    binding = bind_candidate_safety_summary(candidate, bind_token_safety_to_candidate(candidate, observation), summary)
    ledger = EvidenceGroundingLedger()
    ingest_token_safety_candidate_summary_binding(binding, ledger)
    model = build_token_safety_candidate_summary_read_model(ledger)
    assert len(model.rows) == 1
    assert model.rows[0].binding.binding_id == binding.binding_id
    assert model.rows[0].binding.summary.summary_id == summary.summary_id
    assert model.rows[0].replay_verified is True
