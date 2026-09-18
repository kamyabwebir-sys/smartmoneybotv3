from smart_money.application.solana_token_balance_delta import (
    extract_solana_token_balance_deltas,
)


def test_extract_token_balance_delta():
    raw = {
        "meta": {
            "preTokenBalances": [{
                "accountIndex": 1, "mint": "MINT", "owner": "WALLET",
                "uiTokenAmount": {"amount": "10", "decimals": 2},
            }],
            "postTokenBalances": [{
                "accountIndex": 1, "mint": "MINT", "owner": "WALLET",
                "uiTokenAmount": {"amount": "35", "decimals": 2},
            }],
        }
    }
    delta = extract_solana_token_balance_deltas(raw)[0]
    assert delta.delta == 25
    assert delta.pre_amount == 10
    assert delta.post_amount == 35
    assert delta.delta_id


def test_extracts_created_account_as_positive_delta():
    raw = {
        "meta": {
            "preTokenBalances": [],
            "postTokenBalances": [{
                "accountIndex": 2, "mint": "MINT", "owner": "WALLET",
                "uiTokenAmount": {"amount": "7", "decimals": 0},
            }],
        }
    }
    assert extract_solana_token_balance_deltas(raw)[0].delta == 7
