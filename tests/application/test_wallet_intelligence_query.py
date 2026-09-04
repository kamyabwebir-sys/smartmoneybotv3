from smart_money.application.wallet_intelligence_projection import (
    project_wallet_activity_to_intelligence,
)
from smart_money.application.wallet_intelligence_query import query_wallet_intelligence
from smart_money.application.wallet_intelligence_read_model import (
    build_wallet_intelligence_read_model,
)
from smart_money.application.wallet_intelligence_ledger import (
    ingest_wallet_intelligence_observation,
)
from smart_money.application.solana_wallet_activity_aggregation import (
    SolanaWalletActivityAggregate,
)
from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.core.ids import deterministic_id


def test_query_wallet_intelligence_filters_overlap_and_completeness() -> None:
    aggregate = SolanaWalletActivityAggregate(
        wallet="W",
        activity_count=2,
        buy_count=1,
        sell_count=1,
        unknown_count=0,
        token_count=1,
        token_delta_total=3,
        native_delta_total=-1,
        first_slot=10,
        last_slot=20,
        aggregate_id=deterministic_id(
            "solana_wallet_activity_aggregate",
            {
                "activity_count": 2,
                "buy_count": 1,
                "first_slot": 10,
                "last_slot": 20,
                "native_delta_total": -1,
                "schema_version": "solana_wallet_activity_aggregate.v1",
                "sell_count": 1,
                "token_count": 1,
                "token_delta_total": 3,
                "unknown_count": 0,
                "wallet": "W",
            },
        ),
    )
    observation = project_wallet_activity_to_intelligence(aggregate)
    ledger = EvidenceGroundingLedger()
    ingest_wallet_intelligence_observation(observation, ledger)
    model = build_wallet_intelligence_read_model(ledger)

    result = query_wallet_intelligence(
        model, wallet=" W ", min_from_slot=15, max_to_slot=25, min_completeness_bps=10000
    )
    assert len(result.rows) == 1
    assert result.rows[0].observation.wallet == "W"
    assert result.query_id
    assert query_wallet_intelligence(model, wallet="OTHER").rows == ()
