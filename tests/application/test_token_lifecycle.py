import pytest

from smart_money.application.token_lifecycle import (
    TokenLifecycleState,
    advance_token_lifecycle,
    build_token_lifecycle,
)


def test_token_lifecycle_advances_without_regression() -> None:
    created = build_token_lifecycle("evm:bsc:token", TokenLifecycleState.CREATED, 10, ("e1",))
    liquidity = advance_token_lifecycle(
        created, state=TokenLifecycleState.FIRST_LIQUIDITY, observed_slot=12, evidence_ids=("e1", "e2")
    )
    assert liquidity.token_id == created.token_id
    assert liquidity.state is TokenLifecycleState.FIRST_LIQUIDITY


def test_token_lifecycle_rejects_regression() -> None:
    current = build_token_lifecycle("evm:bsc:token", TokenLifecycleState.FIRST_LIQUIDITY, 10, ("e1",))
    with pytest.raises(ValueError):
        advance_token_lifecycle(current, state=TokenLifecycleState.CREATED, observed_slot=11, evidence_ids=("e2",))
