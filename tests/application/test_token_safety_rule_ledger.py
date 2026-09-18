from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.token_safety_parser import parse_token_safety_observation
from smart_money.application.token_safety_rule_evaluation import evaluate_token_safety_rules
from smart_money.application.token_safety_rule_ledger import ingest_token_safety_rule_evaluation


def test_rule_evaluation_projection_is_idempotent():
    observation = parse_token_safety_observation({
        "token": "TOKEN", "observed_at": 10, "mint_authority": "AUTH",
        "freeze_authority": None, "update_authority": None,
        "liquidity_amount": 1, "holder_concentration_bps": 7000, "deployer": "DEPLOYER",
    })
    evaluation = evaluate_token_safety_rules(observation, min_liquidity_amount=100)[0]
    ledger = EvidenceGroundingLedger()
    first = ingest_token_safety_rule_evaluation(evaluation, ledger)
    second = ingest_token_safety_rule_evaluation(evaluation, ledger)
    assert first.evidence_id == second.evidence_id
    assert second.already_present is True
    assert ledger.entry_count == 1
