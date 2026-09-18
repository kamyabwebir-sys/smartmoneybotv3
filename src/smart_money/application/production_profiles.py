from __future__ import annotations

from dataclasses import dataclass

from smart_money.application.wallet_intelligence_profile import (
    WalletIntelligenceProfile,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class WalletProductionProfile:
    wallet: str
    profile_id: str
    observation_count: int
    data_completeness_bps: int
    activity_count: int
    buy_count: int
    sell_count: int
    production_id: str
    schema_version: str = "wallet_production_profile.v1"


def build_wallet_production_profile(
    profile: WalletIntelligenceProfile,
) -> WalletProductionProfile:
    if not isinstance(profile, WalletIntelligenceProfile):
        raise TypeError("profile must be WalletIntelligenceProfile")
    identity = {
        "activity_count": profile.activity_count,
        "buy_count": profile.buy_count,
        "data_completeness_bps": profile.data_completeness_bps,
        "observation_count": profile.observation_count,
        "profile_id": profile.profile_id,
        "schema_version": "wallet_production_profile.v1",
        "sell_count": profile.sell_count,
        "wallet": profile.wallet.strip(),
    }
    return WalletProductionProfile(
        profile.wallet.strip(),
        profile.profile_id,
        profile.observation_count,
        profile.data_completeness_bps,
        profile.activity_count,
        profile.buy_count,
        profile.sell_count,
        deterministic_id("wallet-production-profile", identity),
    )


__all__ = ["WalletProductionProfile", "build_wallet_production_profile"]
