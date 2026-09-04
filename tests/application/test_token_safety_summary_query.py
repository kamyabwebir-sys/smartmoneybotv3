from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.token_safety_evidence_summary import summarize_token_safety_evidence
from smart_money.application.token_safety_parser import parse_token_safety_observation
from smart_money.application.token_safety_rule_evaluation import evaluate_token_safety_rules
from smart_money.application.token_safety_summary_ledger import ingest_token_safety_evidence_summary
from smart_money.application.token_safety_summary_query import query_token_safety_summaries
from smart_money.application.token_safety_summary_read_model import build_token_safety_summary_read_model


def test_summary_query_filters_trigger_count_and_rule_id():
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
    result = query_token_safety_summaries(
        model,
        observation_id=observation.observation_id,
        min_triggered_rules=4,
        required_rule_ids=("authority.active",),
    )
    assert len(result.rows) == 1
    assert result.rows[0].summary.summary_id == summary.summary_id
    assert result.query_id
