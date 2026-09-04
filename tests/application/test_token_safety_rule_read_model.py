from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.token_safety_parser import parse_token_safety_observation
from smart_money.application.token_safety_rule_evaluation import evaluate_token_safety_rules
from smart_money.application.token_safety_rule_ledger import ingest_token_safety_rule_evaluation
from smart_money.application.token_safety_rule_read_model import build_token_safety_rule_read_model


def test_rule_read_model_reconstructs_and_replays():
    observation = parse_token_safety_observation({
        "token": "TOKEN", "observed_at": 10, "mint_authority": "AUTH",
        "freeze_authority": None, "update_authority": None,
        "liquidity_amount": 1, "holder_concentration_bps": 7000, "deployer": "DEPLOYER",
    })
    evaluation = evaluate_token_safety_rules(observation, min_liquidity_amount=100)[0]
    ledger = EvidenceGroundingLedger()
    ingest_token_safety_rule_evaluation(evaluation, ledger)
    model = build_token_safety_rule_read_model(ledger)
    assert len(model.rows) == 1
    assert model.rows[0].evaluation.rule_id == "authority.active"
    assert model.rows[0].replay_verified is True
