from __future__ import annotations

import json
from pathlib import Path

import pytest

from smart_money.adapters.solana_signature_normalizer import (
    SolanaSignatureNormalizer,
    TradeDirection,
)
from smart_money.domain.solana_observation import SolanaChainObservation


def _buy_payload() -> dict[str, object]:
    wallet = "wallet-1"
    quote = "So11111111111111111111111111111111111111112"
    asset = "mint-1"
    return {
        "slot": 42,
        "blockTime": 100,
        "transaction": {
            "signatures": ["signature-1"],
            "message": {
                "accountKeys": [{"pubkey": wallet, "signer": True}],
                "instructions": [
                    {
                        "programId": "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK"
                    }
                ],
            },
        },
        "meta": {
            "fee": 5_000,
            "preBalances": [2_000_000_000],
            "postBalances": [1_999_995_000],
            "preTokenBalances": [
                {
                    "accountIndex": 1,
                    "mint": quote,
                    "owner": wallet,
                    "uiTokenAmount": {"amount": "1000000000", "decimals": 9},
                },
                {
                    "accountIndex": 2,
                    "mint": asset,
                    "owner": wallet,
                    "uiTokenAmount": {"amount": "0", "decimals": 6},
                },
            ],
            "postTokenBalances": [
                {
                    "accountIndex": 1,
                    "mint": quote,
                    "owner": wallet,
                    "uiTokenAmount": {"amount": "900000000", "decimals": 9},
                },
                {
                    "accountIndex": 2,
                    "mint": asset,
                    "owner": wallet,
                    "uiTokenAmount": {"amount": "2500000", "decimals": 6},
                },
            ],
            "innerInstructions": [],
        },
    }


def test_normalizer_produces_typed_deterministic_buy_observation() -> None:
    first = SolanaSignatureNormalizer.normalize(_buy_payload())
    second = SolanaSignatureNormalizer.normalize(_buy_payload())

    assert first == second
    assert isinstance(first.observation, SolanaChainObservation)
    assert first.classification.direction is TradeDirection.BUY
    assert first.classification.reason == "quote_out_asset_in"
    assert len(first.token_deltas) == 2
    assert first.observation.subject == "wallet-1"
    assert first.observation.facts["dex_venues"] == ("RAYDIUM_CLMM",)
    assert first.observation.observation_id == second.observation.observation_id


def test_real_mainnet_fixture_normalizes_to_canonical_observation() -> None:
    path = Path("fixtures/solana/mainnet/s12-trending-buy-candidate.json")
    payload = json.loads(path.read_text(encoding="utf-8"))

    normalized = SolanaSignatureNormalizer.normalize(payload)

    assert normalized.raw.signature
    assert normalized.raw.slot > 0
    assert normalized.raw.signer
    assert normalized.token_deltas
    assert normalized.observation.schema_version == "solana_chain_observation.v1"
    assert normalized.observation.canonical_dict()["facts"]["token_balance_deltas"]


def test_normalizer_fails_closed_on_misaligned_native_balances() -> None:
    payload = _buy_payload()
    payload["meta"]["postBalances"] = []  # type: ignore[index]

    with pytest.raises(ValueError, match="aligned"):
        SolanaSignatureNormalizer.normalize(payload)

