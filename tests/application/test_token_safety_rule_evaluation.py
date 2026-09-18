from smart_money.application.token_safety_parser import parse_token_safety_observation
from smart_money.application.token_safety_rule_evaluation import (
    evaluate_token_safety_rules,
)


def test_token_safety_rules_are_explicit_and_deterministic():
    observation = parse_token_safety_observation(
        {
            "token": "TOKEN",
            "observed_at": 10,
            "mint_authority": "AUTH",
            "freeze_authority": None,
            "update_authority": None,
            "liquidity_amount": 10,
            "holder_concentration_bps": 7000,
            "deployer": "DEPLOYER",
        }
    )
    first = evaluate_token_safety_rules(
        observation, min_liquidity_amount=100, max_holder_concentration_bps=5000
    )
    second = evaluate_token_safety_rules(
        observation, min_liquidity_amount=100, max_holder_concentration_bps=5000
    )
    assert first == second
    assert {item.rule_id for item in first} == {
        "authority.active",
        "liquidity.below_threshold",
        "concentration.above_threshold",
        "deployer.observed",
    }
    assert all(item.triggered for item in first)


def test_token_safety_rule_can_be_untriggered():
    observation = parse_token_safety_observation(
        {
            "token": "TOKEN",
            "observed_at": 10,
            "mint_authority": None,
            "freeze_authority": None,
            "update_authority": None,
            "liquidity_amount": 1000,
            "holder_concentration_bps": 100,
            "deployer": "DEPLOYER",
        }
    )
    evaluations = evaluate_token_safety_rules(observation)
    assert evaluations[0].triggered is False
    assert evaluations[1].triggered is False
    assert evaluations[2].triggered is False
    assert evaluations[3].triggered is True
