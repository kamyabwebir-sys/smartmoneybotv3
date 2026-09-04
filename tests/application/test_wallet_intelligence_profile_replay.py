from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.solana_wallet_activity_aggregation import SolanaWalletActivityAggregate
from smart_money.application.wallet_intelligence_ledger import ingest_wallet_intelligence_observation
from smart_money.application.wallet_intelligence_profile import project_wallet_intelligence_profiles
from smart_money.application.wallet_intelligence_profile_ledger import ingest_wallet_intelligence_profile
from smart_money.application.wallet_intelligence_profile_replay import replay_verify_wallet_intelligence_profile
from smart_money.application.wallet_intelligence_projection import project_wallet_activity_to_intelligence
from smart_money.application.wallet_intelligence_read_model import build_wallet_intelligence_read_model
from smart_money.core.ids import deterministic_id


def test_wallet_intelligence_profile_replays_from_observations() -> None:
    identity = {
        "activity_count": 2, "buy_count": 1, "first_slot": 10, "last_slot": 20,
        "native_delta_total": -1, "schema_version": "solana_wallet_activity_aggregate.v1",
        "sell_count": 1, "token_count": 1, "token_delta_total": 3,
        "unknown_count": 0, "wallet": "W",
    }
    aggregate = SolanaWalletActivityAggregate(
        wallet="W", activity_count=2, buy_count=1, sell_count=1, unknown_count=0,
        token_count=1, token_delta_total=3, native_delta_total=-1,
        first_slot=10, last_slot=20,
        aggregate_id=deterministic_id("solana_wallet_activity_aggregate", identity),
    )
    ledger = EvidenceGroundingLedger()
    observation = project_wallet_activity_to_intelligence(aggregate)
    ingest_wallet_intelligence_observation(observation, ledger)
    profile = project_wallet_intelligence_profiles(build_wallet_intelligence_read_model(ledger))[0]
    ingest_wallet_intelligence_profile(profile, ledger)
    receipt = replay_verify_wallet_intelligence_profile(profile, ledger)
    assert receipt.matches is True
    assert receipt.evidence_id
