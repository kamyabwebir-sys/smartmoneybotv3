import pytest

from smart_money.application.solana_candidate_discovery import SolanaWalletTokenCandidate
from smart_money.application.token_safety_candidate_binding import bind_token_safety_to_candidate
from smart_money.application.token_safety_candidate_summary_binding import bind_candidate_safety_summary
from smart_money.application.token_safety_evidence_summary import summarize_token_safety_evidence
from smart_money.application.token_safety_parser import parse_token_safety_observation
from smart_money.application.token_safety_rule_evaluation import evaluate_token_safety_rules
from smart_money.core.ids import deterministic_id


def _candidate(mint: str = "TOKEN") -> SolanaWalletTokenCandidate:
    identity = {
        "activity_count": 1, "buy_count": 1, "first_slot": 4, "last_slot": 4,
        "mint": mint, "reasons": ("buy_count=1",),
        "schema_version": "solana_wallet_token_candidate.v1", "wallet": "W",
    }
    return SolanaWalletTokenCandidate(
        wallet="W", mint=mint, activity_count=1, buy_count=1,
        first_slot=4, last_slot=4, reasons=("buy_count=1",),
        candidate_id=deterministic_id("solana_wallet_token_candidate", identity),
    )


def _summary(token: str = "TOKEN"):
    observation = parse_token_safety_observation({
        "token": token, "observed_at": 10, "mint_authority": None,
        "freeze_authority": None, "update_authority": "U",
        "liquidity_amount": 1000, "holder_concentration_bps": 1200, "deployer": "D",
    })
    return observation, summarize_token_safety_evidence(evaluate_token_safety_rules(observation))


def test_candidate_binding_includes_summary():
    candidate = _candidate()
    observation, summary = _summary()
    binding = bind_token_safety_to_candidate(candidate, observation)
    result = bind_candidate_safety_summary(candidate, binding, summary)
    assert result.candidate.candidate_id == candidate.candidate_id
    assert result.binding.token_observation_id == observation.observation_id
    assert result.summary.summary_id == summary.summary_id
    assert result.binding_id


def test_candidate_binding_rejects_summary_for_other_observation():
    candidate = _candidate()
    observation, _ = _summary()
    other_observation, other_summary = _summary("OTHER")
    binding = bind_token_safety_to_candidate(candidate, observation)
    with pytest.raises(ValueError, match="observation"):
        bind_candidate_safety_summary(candidate, binding, other_summary)
