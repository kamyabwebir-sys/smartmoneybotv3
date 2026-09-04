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


def test_summary_projection_is_idempotent_and_preserves_evidence():
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
    summary = summarize_token_safety_evidence(
        evaluate_token_safety_rules(observation, min_liquidity_amount=100)
    )
    ledger = EvidenceGroundingLedger()
    first = ingest_token_safety_evidence_summary(summary, ledger)
    second = ingest_token_safety_evidence_summary(summary, ledger)
    payload = ledger.get(first.evidence_id)
    assert first.evidence_id == second.evidence_id
    assert second.already_present is True
    assert payload is not None
    assert payload.data["summary"]["triggered_rules"] == 4
    assert payload.metadata["provenance"]["observation_id"] == observation.observation_id
