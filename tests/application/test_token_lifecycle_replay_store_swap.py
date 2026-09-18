from smart_money.application.first_meaningful_swap import detect_first_meaningful_swap
from smart_money.application.first_liquidity_detection import detect_first_liquidity
from smart_money.application.token_lifecycle_ledger_projection import TokenLifecycleLedgerProjection
from smart_money.application.token_lifecycle_observation_binding import bind_first_liquidity_observation
from smart_money.application.token_lifecycle_replay import verify_token_lifecycle_replay
from smart_money.application.token_lifecycle_store import TokenLifecycleStore


def test_replay_store_and_swap(tmp_path) -> None:
    obs = detect_first_liquidity("t", "p", 10, 2, "rpc")
    binding = bind_first_liquidity_observation(obs)
    projection = TokenLifecycleLedgerProjection.from_binding(binding)
    assert verify_token_lifecycle_replay(binding, projection).replay_matches
    store = TokenLifecycleStore(tmp_path / "lifecycle.json")
    store.save(binding.lifecycle)
    restored = TokenLifecycleStore(tmp_path / "lifecycle.json")
    restored.load()
    assert restored.get(binding.lifecycle.lifecycle_id) == binding.lifecycle
    swap = detect_first_meaningful_swap("t", "w", 1, 3, "rpc")
    assert swap.amount_units == 1
