from smart_money.application.solana_wallet_token_activity import (
    SolanaWalletTokenActivityEvidence,
)
from smart_money.application.wallet_holding_duration import (
    build_wallet_holding_duration_profile,
)
from smart_money.core.ids import deterministic_id


def activity(direction: str, delta: int, slot: int, marker: str):
    identity = {
        "direction": direction,
        "mint": "M",
        "native_delta": 0,
        "schema_version": "solana_wallet_token_activity.v1",
        "slot": slot,
        "token_delta": delta,
        "transaction_signature": marker,
        "wallet": "W",
    }
    return SolanaWalletTokenActivityEvidence(
        activity_id=deterministic_id("solana_wallet_token_activity", identity),
        **identity,
    )


def test_fifo_holding_duration_is_integer_and_replay_stable() -> None:
    values = (
        activity("BUY", 100, 10, "a"),
        activity("BUY", 50, 20, "b"),
        activity("SELL", -120, 40, "c"),
    )

    first = build_wallet_holding_duration_profile(values)
    replay = build_wallet_holding_duration_profile(tuple(reversed(values)))

    assert first == replay
    assert first.closed_lot_count == 2
    assert first.open_lot_count == 1
    assert first.total_held_slots == 50
    assert first.mean_held_slots == 25
    assert (first.minimum_held_slots, first.maximum_held_slots) == (20, 30)


def test_open_position_has_no_invented_duration() -> None:
    profile = build_wallet_holding_duration_profile((activity("BUY", 10, 5, "a"),))
    assert profile.closed_lot_count == 0
    assert profile.open_lot_count == 1
    assert profile.minimum_held_slots is None
