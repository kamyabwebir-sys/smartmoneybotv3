from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.token_safety_ledger_projection import ingest_token_safety_observation
from smart_money.application.token_safety_parser import parse_token_safety_observation
from smart_money.application.token_safety_read_model import build_token_safety_read_model


def test_token_safety_read_model_reconstructs_and_verifies():
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
    ingest_token_safety_observation(observation, ledger)
    model = build_token_safety_read_model(ledger)
    assert len(model.rows) == 1
    assert model.rows[0].observation.token == "TOKEN"
    assert model.rows[0].replay_verified is True
    assert model.model_id
