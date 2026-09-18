import pytest

from smart_money.application.token_safety_parser import parse_token_safety_observation
from smart_money.application.token_safety_rule_evaluation import evaluate_token_safety_rules
from smart_money.application.token_safety_evidence_summary import (
    summarize_token_safety_evidence,
)
from smart_money.core.ids import deterministic_id


def test_token_safety_summary_is_deterministic_and_explainable():
    observation = parse_token_safety_observation(
        {
            "token": "TOKEN",
            "observed_at": 10,
            "mint_authority": "AUTH",
            "freeze_authority": None,
            "update_authority": None,
            "liquidity_amount": 1,
            "holder_concentration_bps": 7000,
            "deployer": "DEPLOYER",
        }
    )
    evaluations = evaluate_token_safety_rules(observation, min_liquidity_amount=100)
    first = summarize_token_safety_evidence(evaluations)
    second = summarize_token_safety_evidence(tuple(reversed(evaluations)))
    assert first == second
    assert first.total_rules == 4
    assert first.triggered_rules == 4
    assert "authority.active" in first.triggered_rule_ids
    assert first.triggered_reasons


def test_summary_rejects_mixed_observations():
    observation = parse_token_safety_observation(
        {
            "token": "TOKEN",
            "observed_at": 10,
            "mint_authority": None,
            "freeze_authority": None,
            "update_authority": None,
            "liquidity_amount": 1,
            "holder_concentration_bps": 100,
            "deployer": "DEPLOYER",
        }
    )
    evaluations = evaluate_token_safety_rules(observation)
    with pytest.raises(ValueError, match="one observation"):
        summarize_token_safety_evidence(
            (evaluations[0], evaluations[0].__class__(
                observation_id="other",
                rule_id=evaluations[1].rule_id,
                triggered=evaluations[1].triggered,
                reason=evaluations[1].reason,
                evaluation_id=deterministic_id(
                    "token_safety_rule_evaluation",
                    {
                        "observation_id": "other",
                        "reason": evaluations[1].reason,
                        "rule_id": evaluations[1].rule_id,
                        "schema_version": evaluations[1].schema_version,
                        "triggered": evaluations[1].triggered,
                    },
                ),
            ))
        )
