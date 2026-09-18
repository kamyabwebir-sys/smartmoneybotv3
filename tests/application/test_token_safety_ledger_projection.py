from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.token_safety_ledger_projection import (
    ingest_token_safety_observation,
)
from smart_money.application.token_safety_parser import parse_token_safety_observation


def test_token_safety_projection_is_idempotent_and_preserves_evidence():
    observation = parse_token_safety_observation(
        {
            "token": "TOKEN",
            "observed_at": 10,
            "mint_authority": None,
            "freeze_authority": None,
            "update_authority": "UPDATER",
            "liquidity_amount": 1000,
            "holder_concentration_bps": 1200,
            "deployer": "DEPLOYER",
        }
    )
    ledger = EvidenceGroundingLedger()
    first = ingest_token_safety_observation(observation, ledger)
    second = ingest_token_safety_observation(observation, ledger)
    payload = ledger.get(first.evidence_id)
    assert first.evidence_id == second.evidence_id
    assert second.already_present is True
    assert ledger.entry_count == 1
    assert payload is not None
    assert payload.data["token_safety"]["holder_concentration_bps"] == 1200
    assert payload.metadata["verification_status"] == "PROVISIONAL"
