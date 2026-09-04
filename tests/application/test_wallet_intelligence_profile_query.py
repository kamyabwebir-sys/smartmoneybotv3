from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.solana_wallet_activity_aggregation import SolanaWalletActivityAggregate
from smart_money.application.wallet_intelligence_ledger import ingest_wallet_intelligence_observation
from smart_money.application.wallet_intelligence_profile import project_wallet_intelligence_profiles
from smart_money.application.wallet_intelligence_projection import project_wallet_activity_to_intelligence
from smart_money.application.wallet_intelligence_profile_query import query_wallet_intelligence_profiles
from smart_money.application.wallet_intelligence_read_model import build_wallet_intelligence_read_model
from smart_money.core.ids import deterministic_id


def test_profile_query_filters_activity_buy_ratio_completeness_and_window() -> None:
    identity = {
        "activity_count": 3, "buy_count": 2, "first_slot": 1, "last_slot": 9,
        "native_delta_total": -10, "schema_version": "solana_wallet_activity_aggregate.v1",
        "sell_count": 1, "token_count": 2, "token_delta_total": 30,
        "unknown_count": 0, "wallet": "W",
    }
    aggregate = SolanaWalletActivityAggregate(
        wallet="W", activity_count=3, buy_count=2, sell_count=1, unknown_count=0,
        token_count=2, token_delta_total=30, native_delta_total=-10,
        first_slot=1, last_slot=9,
        aggregate_id=deterministic_id("solana_wallet_activity_aggregate", identity),
    )
    observation = project_wallet_activity_to_intelligence(aggregate)
    ledger = EvidenceGroundingLedger()
    ingest_wallet_intelligence_observation(observation, ledger)
    profiles = project_wallet_intelligence_profiles(build_wallet_intelligence_read_model(ledger))
    result = query_wallet_intelligence_profiles(
        profiles,
        min_activity_count=3,
        min_buy_ratio_bps=6666,
        min_completeness_bps=10000,
        min_observed_from_slot=5,
        max_observed_to_slot=10,
    )
    assert result.profiles == profiles
    assert result.query_id
    assert query_wallet_intelligence_profiles(profiles, min_buy_ratio_bps=7000).profiles == ()
