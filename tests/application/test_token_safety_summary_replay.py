import pytest

from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.token_safety_evidence_summary import (
    summarize_token_safety_evidence,
)
from smart_money.application.token_safety_parser import parse_token_safety_observation
from smart_money.application.token_safety_rule_evaluation import (
    evaluate_token_safety_rules,
)
from smart_money.application.token_safety_summary_ledger import (
    ingest_token_safety_evidence_summary,
)
from smart_money.application.token_safety_summary_replay import (
    replay_verify_token_safety_evidence_summary,
)


def _summary():
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
    return summarize_token_safety_evidence(
        evaluate_token_safety_rules(observation, min_liquidity_amount=100)
    )


def test_summary_replay_matches_ledger():
    summary = _summary()
    ledger = EvidenceGroundingLedger()
    ingest_token_safety_evidence_summary(summary, ledger)
    receipt = replay_verify_token_safety_evidence_summary(summary, ledger)
    assert receipt.matches is True
    assert receipt.summary_id == summary.summary_id


def test_summary_replay_fails_when_missing():
    with pytest.raises(ValueError, match="missing"):
        replay_verify_token_safety_evidence_summary(_summary(), EvidenceGroundingLedger())
