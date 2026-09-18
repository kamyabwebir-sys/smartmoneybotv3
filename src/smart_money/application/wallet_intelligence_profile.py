from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_intelligence_read_model import (
    WalletIntelligenceReadModel,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_intelligence_profile.v1"


@dataclass(frozen=True, slots=True)
class WalletIntelligenceProfile:
    wallet: str
    observation_count: int
    observed_from_slot: int
    observed_to_slot: int
    activity_count: int
    buy_count: int
    sell_count: int
    unknown_count: int
    distinct_token_observation_total: int
    token_delta_total: int
    native_delta_total: int
    data_completeness_bps: int
    observation_ids: tuple[str, ...]
    profile_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.wallet, str) or not self.wallet.strip():
            raise ValueError("wallet must be non-empty")
        for name in ("observation_count", "observed_from_slot", "observed_to_slot",
                     "activity_count", "buy_count", "sell_count", "unknown_count",
                     "distinct_token_observation_total"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        for name in ("token_delta_total", "native_delta_total"):
            if isinstance(getattr(self, name), bool) or not isinstance(getattr(self, name), int):
                raise TypeError(f"{name} must be an integer")
        if self.observed_to_slot < self.observed_from_slot:
            raise ValueError("observed slot range is reversed")
        if self.activity_count != self.buy_count + self.sell_count + self.unknown_count:
            raise ValueError("activity counts do not reconcile")
        if self.observation_count != len(self.observation_ids) or self.observation_count < 1:
            raise ValueError("observation_ids must match observation_count")
        if not all(isinstance(item, str) and item.strip() for item in self.observation_ids):
            raise ValueError("observation_ids must contain non-empty strings")
        if not 0 <= self.data_completeness_bps <= 10000:
            raise ValueError("data_completeness_bps must be between 0 and 10000")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet intelligence profile schema_version")
        if self.profile_id != deterministic_id(
            "wallet_intelligence_profile", self.identity_payload()
        ):
            raise ValueError("profile_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "activity_count": self.activity_count,
            "buy_count": self.buy_count,
            "data_completeness_bps": self.data_completeness_bps,
            "distinct_token_observation_total": self.distinct_token_observation_total,
            "native_delta_total": self.native_delta_total,
            "observed_from_slot": self.observed_from_slot,
            "observed_to_slot": self.observed_to_slot,
            "observation_count": self.observation_count,
            "observation_ids": self.observation_ids,
            "schema_version": self.schema_version,
            "sell_count": self.sell_count,
            "token_delta_total": self.token_delta_total,
            "unknown_count": self.unknown_count,
            "wallet": self.wallet.strip(),
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"profile_id": self.profile_id, **self.identity_payload()}


def project_wallet_intelligence_profiles(
    model: WalletIntelligenceReadModel,
) -> tuple[WalletIntelligenceProfile, ...]:
    if not isinstance(model, WalletIntelligenceReadModel):
        raise TypeError("model must be WalletIntelligenceReadModel")
    grouped: dict[str, list[Any]] = {}
    for row in model.rows:
        grouped.setdefault(row.observation.wallet, []).append(row.observation)
    profiles: list[WalletIntelligenceProfile] = []
    for wallet, observations in grouped.items():
        observations.sort(key=lambda item: (item.observed_from_slot, item.observed_to_slot, item.observation_id))
        total_activity = sum(item.activity_count for item in observations)
        completeness = (
            sum(item.data_completeness_bps * item.activity_count for item in observations) // total_activity
            if total_activity else 0
        )
        identity = {
            "activity_count": total_activity,
            "buy_count": sum(item.buy_count for item in observations),
            "data_completeness_bps": completeness,
            "distinct_token_observation_total": sum(item.distinct_token_count for item in observations),
            "native_delta_total": sum(item.native_delta_total for item in observations),
            "observed_from_slot": observations[0].observed_from_slot,
            "observed_to_slot": max(item.observed_to_slot for item in observations),
            "observation_count": len(observations),
            "observation_ids": tuple(item.observation_id for item in observations),
            "schema_version": _SCHEMA_VERSION,
            "sell_count": sum(item.sell_count for item in observations),
            "token_delta_total": sum(item.token_delta_total for item in observations),
            "unknown_count": sum(item.unknown_count for item in observations),
            "wallet": wallet.strip(),
        }
        profiles.append(WalletIntelligenceProfile(profile_id=deterministic_id("wallet_intelligence_profile", identity), **identity))
    return tuple(sorted(profiles, key=lambda item: item.wallet))


__all__ = ["WalletIntelligenceProfile", "project_wallet_intelligence_profiles"]
