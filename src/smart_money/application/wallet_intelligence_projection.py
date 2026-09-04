from __future__ import annotations

from smart_money.application.solana_wallet_activity_aggregation import (
    SolanaWalletActivityAggregate,
)
from smart_money.core.ids import deterministic_id
from smart_money.domain.wallet_intelligence import WalletIntelligenceObservation


def project_wallet_activity_to_intelligence(
    aggregate: SolanaWalletActivityAggregate,
) -> WalletIntelligenceObservation:
    """Project an existing Wallet activity aggregate into an intelligence observation."""
    if not isinstance(aggregate, SolanaWalletActivityAggregate):
        raise TypeError("aggregate must be SolanaWalletActivityAggregate")
    completeness = 10000 if aggregate.activity_count > 0 else 0
    identity = {
        "activity_count": aggregate.activity_count,
        "buy_count": aggregate.buy_count,
        "data_completeness_bps": completeness,
        "distinct_token_count": aggregate.token_count,
        "native_delta_total": aggregate.native_delta_total,
        "observed_from_slot": aggregate.first_slot,
        "observed_to_slot": aggregate.last_slot,
        "schema_version": "wallet_intelligence_observation.v1",
        "sell_count": aggregate.sell_count,
        "token_delta_total": aggregate.token_delta_total,
        "unknown_count": aggregate.unknown_count,
        "wallet": aggregate.wallet,
    }
    return WalletIntelligenceObservation(
        wallet=aggregate.wallet,
        observed_from_slot=aggregate.first_slot,
        observed_to_slot=aggregate.last_slot,
        activity_count=aggregate.activity_count,
        buy_count=aggregate.buy_count,
        sell_count=aggregate.sell_count,
        unknown_count=aggregate.unknown_count,
        distinct_token_count=aggregate.token_count,
        token_delta_total=aggregate.token_delta_total,
        native_delta_total=aggregate.native_delta_total,
        data_completeness_bps=completeness,
        observation_id=deterministic_id("wallet_intelligence_observation", identity),
    )


__all__ = ["project_wallet_activity_to_intelligence"]
