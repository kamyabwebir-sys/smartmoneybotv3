import pytest

from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.token_safety_parser import parse_token_safety_observation
from smart_money.application.token_safety_rule_evaluation import evaluate_token_safety_rules
from smart_money.application.token_safety_rule_ledger import ingest_token_safety_rule_evaluation
from smart_money.application.token_safety_rule_replay import replay_verify_token_safety_rule_evaluation


def _evaluation():
    observation = parse_token_safety_observation({
        "token": "TOKEN", "observed_at": 10, "mint_authority": "AUTH",
        "freeze_authority": None, "update_authority": None,
        "liquidity_amount": 1, "holder_concentration_bps": 7000, "deployer": "DEPLOYER",
    })
    return evaluate_token_safety_rules(observation, min_liquidity_amount=100)[0]


def test_rule_replay_matches_ledger():
    evaluation = _evaluation()
    ledger = EvidenceGroundingLedger()
    ingest_token_safety_rule_evaluation(evaluation, ledger)
    receipt = replay_verify_token_safety_rule_evaluation(evaluation, ledger)
    assert receipt.matches is True
    assert receipt.evaluation_id == evaluation.evaluation_id


def test_rule_replay_fails_when_missing():
    with pytest.raises(ValueError, match="missing"):
        replay_verify_token_safety_rule_evaluation(_evaluation(), EvidenceGroundingLedger())
