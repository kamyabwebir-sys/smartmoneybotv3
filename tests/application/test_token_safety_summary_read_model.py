from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.token_safety_evidence_summary import summarize_token_safety_evidence
from smart_money.application.token_safety_parser import parse_token_safety_observation
from smart_money.application.token_safety_rule_evaluation import evaluate_token_safety_rules
from smart_money.application.token_safety_summary_ledger import ingest_token_safety_evidence_summary
from smart_money.application.token_safety_summary_read_model import build_token_safety_summary_read_model


def test_summary_read_model_reconstructs_and_replays():
    observation = parse_token_safety_observation({
        "token": "TOKEN", "observed_at": 10, "mint_authority": "AUTH",
        "freeze_authority": None, "update_authority": None,
        "liquidity_amount": 1, "holder_concentration_bps": 7000, "deployer": "DEPLOYER",
    })
    summary = summarize_token_safety_evidence(
        evaluate_token_safety_rules(observation, min_liquidity_amount=100)
    )
    ledger = EvidenceGroundingLedger()
    ingest_token_safety_evidence_summary(summary, ledger)
    model = build_token_safety_summary_read_model(ledger)
    assert len(model.rows) == 1
    assert model.rows[0].summary.summary_id == summary.summary_id
    assert model.rows[0].replay_verified is True
    assert model.model_id
