from smart_money.application.first_meaningful_swap import detect_first_meaningful_swap
from smart_money.application.first_liquidity_detection import detect_first_liquidity
from smart_money.application.token_lifecycle_observation_binding import bind_first_liquidity_observation, bind_first_meaningful_swap_observation
from smart_money.application.token_lifecycle_query import query_token_lifecycle
from smart_money.application.token_lifecycle_read_model import build_token_lifecycle_read_model


def test_binding_read_model_query() -> None:
    liquidity = bind_first_liquidity_observation(detect_first_liquidity("t", "p", 10, 2, "rpc"))
    swap = bind_first_meaningful_swap_observation(detect_first_meaningful_swap("t", "w", 2, 3, "rpc"), liquidity.lifecycle)
    result = query_token_lifecycle(build_token_lifecycle_read_model((liquidity.lifecycle, swap.lifecycle)), token_id=" t ")
    assert len(result.rows) == 2
    assert result.query_id
