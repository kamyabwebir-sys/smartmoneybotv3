from smart_money.application.early_entry_consistency import evaluate_early_entry_consistency
from smart_money.application.early_entry_consistency_query import query_early_entry_consistency
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


def test_early_entry_query_filters_consistency_and_samples() -> None:
    value = evaluate_early_entry_consistency(
        (_activity(10, "T1", "S1"), _activity(30, "T2", "S2")),
        reference_slots={"T1": 20, "T2": 20},
    )
    result = query_early_entry_consistency(
        (value,), min_consistency_bps=5000, min_samples=2
    )
    assert result.matches == (value,)
    assert query_early_entry_consistency((value,), min_consistency_bps=6000).matches == ()


def test_early_entry_query_rejects_unsupported_slot_filter() -> None:
    value = evaluate_early_entry_consistency(
        (_activity(10, "T1", "S1"),), reference_slots={"T1": 20}
    )
    assert query_early_entry_consistency((value,), min_observed_slot=1).matches == (value,)
