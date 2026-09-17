from copy import deepcopy

import pytest

from smart_money.application.solana_account_resolution import resolve_solana_accounts


def transaction() -> dict:
    return {
        "transaction": {
            "message": {
                "accountKeys": ["fee-payer", "co-signer"],
                "header": {"numRequiredSignatures": 2},
            }
        },
        "meta": {
            "loadedAddresses": {"writable": ["token-account"], "readonly": ["program"]},
            "preTokenBalances": [{"accountIndex": 2, "owner": "fee-payer", "mint": "mint"}],
            "postTokenBalances": [{"accountIndex": 2, "owner": "fee-payer", "mint": "mint"}],
        },
    }


def test_resolves_signers_loaded_addresses_and_token_owner_deterministically() -> None:
    raw = transaction()
    first = resolve_solana_accounts(raw)
    second = resolve_solana_accounts(deepcopy(raw))

    assert first == second
    assert first.fee_payer == "fee-payer"
    assert first.signers == ("fee-payer", "co-signer")
    assert first.account_keys == ("fee-payer", "co-signer", "token-account", "program")
    assert first.token_account_owners == ((2, "fee-payer", "mint"),)


def test_rejects_owner_conflict() -> None:
    raw = transaction()
    raw["meta"]["postTokenBalances"][0]["owner"] = "other"
    with pytest.raises(ValueError, match="ownership changed"):
        resolve_solana_accounts(raw)
