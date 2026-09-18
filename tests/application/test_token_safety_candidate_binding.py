import pytest

from smart_money.application.solana_candidate_discovery import SolanaWalletTokenCandidate
from smart_money.application.token_safety_candidate_binding import bind_token_safety_to_candidate
from smart_money.application.token_safety_parser import parse_token_safety_observation
from smart_money.core.ids import deterministic_id


def _candidate(mint="TOKEN"):
    identity = {
        "activity_count": 1, "buy_count": 1, "first_slot": 4, "last_slot": 4,
        "mint": mint, "reasons": ("buy_count=1",),
        "schema_version": "solana_wallet_token_candidate.v1", "wallet": "W",
    }
    return SolanaWalletTokenCandidate(
        wallet="W", mint=mint, activity_count=1, buy_count=1, first_slot=4,
        last_slot=4, reasons=("buy_count=1",),
        candidate_id=deterministic_id("solana_wallet_token_candidate", identity),
    )


def _observation(token="TOKEN"):
    return parse_token_safety_observation({
        "token": token, "observed_at": 10, "mint_authority": None,
        "freeze_authority": None, "update_authority": "UPDATER",
        "liquidity_amount": 1000, "holder_concentration_bps": 1200,
        "deployer": "DEPLOYER",
    })


def test_token_safety_binding_preserves_both_identities():
    binding = bind_token_safety_to_candidate(_candidate(), _observation())
    assert binding.wallet == "W"
    assert binding.token == "TOKEN"
    assert binding.liquidity_amount == 1000
    assert binding.candidate_id
    assert binding.token_observation_id


def test_token_safety_binding_rejects_mismatch():
    with pytest.raises(ValueError, match="mismatch"):
        bind_token_safety_to_candidate(_candidate(), _observation("OTHER"))
