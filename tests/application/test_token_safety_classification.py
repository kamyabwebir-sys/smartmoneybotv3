from smart_money.application.token_safety_classification import (
    TokenSafetyEvidenceCategory,
    classify_token_safety_evidence,
)
from smart_money.application.token_safety_parser import parse_token_safety_observation


def test_token_safety_evidence_is_classified_deterministically():
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
    first = classify_token_safety_evidence(observation)
    second = classify_token_safety_evidence(observation)
    assert first == second
    assert {item.category for item in first} == {
        TokenSafetyEvidenceCategory.AUTHORITY,
        TokenSafetyEvidenceCategory.LIQUIDITY,
        TokenSafetyEvidenceCategory.CONCENTRATION,
        TokenSafetyEvidenceCategory.DEPLOYER,
    }
    assert all(item.classification_id for item in first)
