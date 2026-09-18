import pytest

from smart_money.application.solana_swap_evidence import extract_solana_swap_evidence
from smart_money.application.solana_wallet_token_activity import (
    build_solana_wallet_token_activity,
)
from smart_money.domain.solana_observation import SolanaChainObservation


def test_wallet_token_activity_binds_observation_and_swap():
    raw = {
        "slot": 77,
        "transaction": {
            "signatures": ["sig-activity"],
            "message": {"accountKeys": [{"pubkey": "program"}],
            },
        },
        "meta": {
            "preBalances": [1000], "postBalances": [900],
            "preTokenBalances": [{"accountIndex": 1, "mint": "MINT", "owner": "WALLET",
                                  "uiTokenAmount": {"amount": "0", "decimals": 0}}],
            "postTokenBalances": [{"accountIndex": 1, "mint": "MINT", "owner": "WALLET",
                                   "uiTokenAmount": {"amount": "20", "decimals": 0}}],
        },
    }
    observation = SolanaChainObservation(
        slot=77, observed_at=100, transaction_signature="sig-activity",
        program_id="program", subject="program", facts={}
    )
    swap = extract_solana_swap_evidence(raw, owner="WALLET", mint="MINT")
    activity = build_solana_wallet_token_activity(observation, swap)
    assert activity.direction == "BUY"
    assert activity.wallet == "WALLET"
    assert activity.slot == 77
    assert activity.activity_id


def test_wallet_token_activity_rejects_signature_mismatch():
    observation = SolanaChainObservation(
        slot=1, observed_at=1, transaction_signature="other",
        program_id="program", subject="program", facts={}
    )
    raw = {
        "transaction": {"signatures": ["sig"]},
        "meta": {
            "preBalances": [10], "postBalances": [9],
            "preTokenBalances": [{"accountIndex": 1, "mint": "M", "owner": "W",
                                  "uiTokenAmount": {"amount": "0", "decimals": 0}}],
            "postTokenBalances": [{"accountIndex": 1, "mint": "M", "owner": "W",
                                   "uiTokenAmount": {"amount": "1", "decimals": 0}}],
        },
    }
    swap = extract_solana_swap_evidence(raw, owner="W", mint="M")
    with pytest.raises(ValueError, match="signature mismatch"):
        build_solana_wallet_token_activity(observation, swap)
