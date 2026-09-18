from smart_money.application.early_entry_consistency import evaluate_early_entry_consistency
from smart_money.application.solana_wallet_token_activity import SolanaWalletTokenActivityEvidence
from smart_money.core.ids import deterministic_id


def _activity(slot: int, mint: str, signature: str) -> SolanaWalletTokenActivityEvidence:
    identity = {
        "direction": "BUY", "mint": mint, "native_delta": -1,
        "schema_version": "solana_wallet_token_activity.v1", "slot": slot,
        "token_delta": 10, "transaction_signature": signature, "wallet": "W",
    }
    return SolanaWalletTokenActivityEvidence(
        **identity, activity_id=deterministic_id("solana_wallet_token_activity", identity)
    )


def test_early_entry_consistency_is_deterministic() -> None:
    activities = (_activity(10, "T1", "S1"), _activity(30, "T2", "S2"))
    result = evaluate_early_entry_consistency(
        activities, reference_slots={"T1": 20, "T2": 20}
    )
    assert result.evaluated_buy_count == 2
    assert result.early_entry_count == 1
    assert result.consistency_bps == 5000
    assert result == evaluate_early_entry_consistency(
        tuple(reversed(activities)), reference_slots={"T2": 20, "T1": 20}
    )
