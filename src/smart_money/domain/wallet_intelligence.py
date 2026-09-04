from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class WalletIntelligenceObservation:
    wallet: str
    observed_from_slot: int
    observed_to_slot: int
    activity_count: int
    buy_count: int
    sell_count: int
    unknown_count: int
    distinct_token_count: int
    token_delta_total: int
    native_delta_total: int
    data_completeness_bps: int
    observation_id: str
    schema_version: str = "wallet_intelligence_observation.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.wallet, str) or not self.wallet.strip():
            raise ValueError("wallet must be non-empty")
        for name in (
            "observed_from_slot",
            "observed_to_slot",
            "activity_count",
            "buy_count",
            "sell_count",
            "unknown_count",
            "distinct_token_count",
        ):
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
        if self.distinct_token_count > self.activity_count:
            raise ValueError("distinct_token_count cannot exceed activity_count")
        if isinstance(self.data_completeness_bps, bool) or not isinstance(self.data_completeness_bps, int) or not 0 <= self.data_completeness_bps <= 10000:
            raise ValueError("data_completeness_bps must be between 0 and 10000")
        if not isinstance(self.observation_id, str) or not self.observation_id.strip():
            raise ValueError("observation_id must be non-empty")
        if self.schema_version != "wallet_intelligence_observation.v1":
            raise ValueError("unsupported wallet intelligence schema_version")
        if self.observation_id != deterministic_id(
            "wallet_intelligence_observation", self.identity_payload()
        ):
            raise ValueError("observation_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "activity_count": self.activity_count,
            "buy_count": self.buy_count,
            "data_completeness_bps": self.data_completeness_bps,
            "distinct_token_count": self.distinct_token_count,
            "native_delta_total": self.native_delta_total,
            "observed_from_slot": self.observed_from_slot,
            "observed_to_slot": self.observed_to_slot,
            "schema_version": self.schema_version,
            "sell_count": self.sell_count,
            "token_delta_total": self.token_delta_total,
            "unknown_count": self.unknown_count,
            "wallet": self.wallet.strip(),
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"observation_id": self.observation_id, **self.identity_payload()}


__all__ = ["WalletIntelligenceObservation"]
