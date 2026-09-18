from smart_money.application.first_liquidity_detection import detect_first_liquidity
from smart_money.application.token_lifecycle_ledger_projection import TokenLifecycleLedgerProjection
from smart_money.application.token_lifecycle_observation_binding import (
    bind_first_liquidity_observation,
)


def test_first_liquidity_binding_and_ledger_projection() -> None:
    observation = detect_first_liquidity("solana:mainnet-beta:t", "pool", 100, 20, "rpc")
    binding = bind_first_liquidity_observation(observation)
    projection = TokenLifecycleLedgerProjection.from_binding(binding)
    assert binding.lifecycle.state.value == "FIRST_LIQUIDITY"
    assert projection.payload.get_canonical_id()
    assert projection.lifecycle_id == binding.lifecycle.lifecycle_id
