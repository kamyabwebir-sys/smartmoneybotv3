import pytest

from smart_money.application.solana_transaction_decoder import decode_solana_transaction


def _raw():
    return {
        "slot": 42,
        "transaction": {
            "signatures": ["sig-1"],
            "message": {"accountKeys": [{"pubkey": "program-1"}]},
        },
        "meta": {
            "err": None,
            "fee": 5000,
            "preBalances": [10],
            "postBalances": [9],
            "logMessages": ["Program invoke"],
        },
    }


def test_decode_transaction_is_canonical_and_deterministic():
    first = decode_solana_transaction(_raw(), observed_at=100)
    second = decode_solana_transaction(dict(_raw()), observed_at=100)
    assert first == second
    assert first.slot == 42
    assert first.transaction_signature == "sig-1"
    assert first.facts["fee"] == 5000


def test_decode_fails_closed_when_signature_missing():
    raw = _raw()
    raw["transaction"]["signatures"] = []
    with pytest.raises(ValueError, match="signature"):
        decode_solana_transaction(raw, observed_at=100)
