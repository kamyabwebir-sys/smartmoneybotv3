import pytest

from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.token_safety_ledger_projection import ingest_token_safety_observation
from smart_money.application.token_safety_parser import parse_token_safety_observation
from smart_money.application.token_safety_replay import replay_verify_token_safety_observation


def _observation():
    return parse_token_safety_observation(
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


def test_token_safety_replay_matches_ledger():
    observation = _observation()
    ledger = EvidenceGroundingLedger()
    ingest_token_safety_observation(observation, ledger)
    receipt = replay_verify_token_safety_observation(observation, ledger)
    assert receipt.matches is True
    assert receipt.observation_id == observation.observation_id


def test_token_safety_replay_fails_when_missing():
    with pytest.raises(ValueError, match="missing"):
        replay_verify_token_safety_observation(_observation(), EvidenceGroundingLedger())
