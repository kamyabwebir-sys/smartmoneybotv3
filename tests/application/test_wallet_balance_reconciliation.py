from copy import deepcopy

import pytest

from smart_money.application.wallet_balance_reconciliation import reconcile_wallet_balances


def transaction():
    def row(index, mint, amount):
        return {"accountIndex": index, "mint": mint, "owner": "W",
                "uiTokenAmount": {"amount": str(amount), "decimals": 6}}
    return {"transaction": {"signatures": ["sig"], "message": {"accountKeys": ["W", "A", "B", "C"]}},
            "meta": {"err": None, "fee": 5, "preBalances": [100, 0, 0, 0],
                     "postBalances": [95, 0, 0, 0],
                     "preTokenBalances": [row(1, "X", 10), row(2, "Y", 8), row(3, "X", 20)],
                     "postTokenBalances": [row(1, "X", 30), row(2, "Y", 8), row(3, "X", 10)]}}


def test_fee_only_is_not_swap_spend_and_accounts_are_aggregated():
    result = reconcile_wallet_balances(transaction(), "W")
    assert result.native_delta_excluding_fee == 0
    assert result.token_deltas == (("X", 6, 10), ("Y", 6, 0))
    assert "direction" not in result.canonical_dict()


def test_replay_order_and_input_immutability():
    raw = transaction()
    before = deepcopy(raw)
    first = reconcile_wallet_balances(raw, "W")
    assert raw == before
    raw["meta"]["preTokenBalances"].reverse()
    raw["meta"]["postTokenBalances"].reverse()
    assert reconcile_wallet_balances(raw, "W").evidence_id == first.evidence_id


@pytest.mark.parametrize("field,value", [("amount", True), ("amount", "1.1"), ("amount", "-1"),
                                        ("decimals", True), ("decimals", -1), ("decimals", 256)])
def test_rejects_type_confusion(field, value):
    raw = transaction()
    raw["meta"]["preTokenBalances"][0]["uiTokenAmount"][field] = value
    with pytest.raises(ValueError):
        reconcile_wallet_balances(raw, "W")


@pytest.mark.parametrize("case", ["duplicate", "owner", "decimals", "failed", "missing", "unknown_wallet"])
def test_rejects_incomplete_or_conflicting_evidence(case):
    raw = transaction()
    meta = raw["meta"]
    if case == "duplicate":
        meta["preTokenBalances"].append(deepcopy(meta["preTokenBalances"][0]))
    elif case == "owner":
        meta["postTokenBalances"][0]["owner"] = "OTHER"
    elif case == "decimals":
        meta["postTokenBalances"][0]["uiTokenAmount"]["decimals"] = 9
    elif case == "failed":
        meta["err"] = {"InstructionError": [0, "error"]}
    elif case == "missing":
        del meta["preTokenBalances"]
    with pytest.raises(ValueError):
        reconcile_wallet_balances(raw, "absent" if case == "unknown_wallet" else "W")


def test_another_fee_payer_and_new_closed_accounts():
    raw = transaction()
    raw["transaction"]["message"]["accountKeys"][:2] = ["A", "W"]
    raw["meta"]["preTokenBalances"].pop(0)
    raw["meta"]["postTokenBalances"].pop(2)
    result = reconcile_wallet_balances(raw, "W")
    assert result.fee_paid == 0
    assert result.token_deltas == (("X", 6, 10), ("Y", 6, 0))
