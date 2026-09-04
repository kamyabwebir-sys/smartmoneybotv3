from smart_money.application.solana_swap_evidence import extract_solana_swap_evidence


def _raw(token_after: str, native_before: int = 1_000, native_after: int = 900):
    return {
        "transaction": {"signatures": ["sig-swap"]},
        "meta": {
            "preBalances": [native_before],
            "postBalances": [native_after],
            "preTokenBalances": [{
                "accountIndex": 1, "mint": "MINT", "owner": "WALLET",
                "uiTokenAmount": {"amount": "0", "decimals": 0},
            }],
            "postTokenBalances": [{
                "accountIndex": 1, "mint": "MINT", "owner": "WALLET",
                "uiTokenAmount": {"amount": token_after, "decimals": 0},
            }],
        },
    }


def test_positive_token_and_negative_native_is_buy():
    evidence = extract_solana_swap_evidence(_raw("25"), owner="WALLET", mint="MINT")
    assert evidence.direction == "BUY"
    assert evidence.token_delta == 25
    assert evidence.native_delta == -100


def test_ambiguous_flow_is_unknown():
    evidence = extract_solana_swap_evidence(
        _raw("25", native_before=100, native_after=200), owner="WALLET", mint="MINT"
    )
    assert evidence.direction == "UNKNOWN"
