from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.token_safety_parser import parse_token_safety_observation
from smart_money.application.token_safety_rule_evaluation import evaluate_token_safety_rules
from smart_money.application.token_safety_rule_ledger import ingest_token_safety_rule_evaluation
from smart_money.application.token_safety_rule_query import query_token_safety_rules
from smart_money.application.token_safety_rule_read_model import build_token_safety_rule_read_model


def test_token_safety_rule_query_filters_triggered_rules():
    observation = parse_token_safety_observation({
        "token": "TOKEN", "observed_at": 10, "mint_authority": "AUTH",
        "freeze_authority": None, "update_authority": None,
        "liquidity_amount": 1, "holder_concentration_bps": 100, "deployer": "DEPLOYER",
    })
    evaluations = evaluate_token_safety_rules(observation, min_liquidity_amount=100)
    ledger = EvidenceGroundingLedger()
    for evaluation in evaluations:
        ingest_token_safety_rule_evaluation(evaluation, ledger)
    model = build_token_safety_rule_read_model(ledger)
    result = query_token_safety_rules(
        model, observation_id=observation.observation_id, triggered=True
    )
    assert len(result.rows) == 3
    assert all(row.evaluation.triggered for row in result.rows)
    assert result.query_id
