from smart_money.application.solana_wallet_activity_aggregation import (
    SolanaWalletActivityAggregate,
)
from smart_money.application.wallet_intelligence_projection import (
    project_wallet_activity_to_intelligence,
)
from smart_money.core.ids import deterministic_id


def test_wallet_aggregate_projects_to_intelligence_observation():
    identity = {
        "activity_count": 3,
        "buy_count": 2,
        "first_slot": 1,
        "last_slot": 9,
        "native_delta_total": -10,
        "schema_version": "solana_wallet_activity_aggregate.v1",
        "sell_count": 1,
        "token_count": 2,
        "token_delta_total": 30,
        "unknown_count": 0,
        "wallet": "W",
    }
    aggregate = SolanaWalletActivityAggregate(
        wallet="W",
        activity_count=3,
        buy_count=2,
        sell_count=1,
        unknown_count=0,
        token_count=2,
        token_delta_total=30,
        native_delta_total=-10,
        first_slot=1,
        last_slot=9,
        aggregate_id=deterministic_id("solana_wallet_activity_aggregate", identity),
    )
    observation = project_wallet_activity_to_intelligence(aggregate)
    assert observation.wallet == "W"
    assert observation.activity_count == 3
    assert observation.data_completeness_bps == 10000
    assert observation.observation_id
