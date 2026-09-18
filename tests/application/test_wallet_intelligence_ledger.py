from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.wallet_intelligence_ledger import (
    ingest_wallet_intelligence_observation,
)
from smart_money.application.wallet_intelligence_projection import (
    project_wallet_activity_to_intelligence,
)
from smart_money.application.solana_wallet_activity_aggregation import (
    SolanaWalletActivityAggregate,
)
from smart_money.core.ids import deterministic_id


def test_wallet_intelligence_projection_is_idempotent():
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
    ledger = EvidenceGroundingLedger()
    first = ingest_wallet_intelligence_observation(observation, ledger)
    second = ingest_wallet_intelligence_observation(observation, ledger)
    assert first.evidence_id == second.evidence_id
    assert second.already_present is True
    assert ledger.entry_count == 1
    payload = ledger.get(first.evidence_id)
    assert payload is not None
    assert payload.data["wallet_intelligence"]["wallet"] == "W"
    assert payload.metadata["verification_status"] == "PROVISIONAL"
