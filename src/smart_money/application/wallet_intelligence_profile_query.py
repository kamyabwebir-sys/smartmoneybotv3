from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_intelligence_profile import (
    WalletIntelligenceProfile,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_intelligence_profile_query.v1"


@dataclass(frozen=True, slots=True)
class WalletIntelligenceProfileQueryResult:
    profiles: tuple[WalletIntelligenceProfile, ...]
    query_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.profiles, tuple):
            raise TypeError("profiles must be a tuple")
        if not isinstance(self.query_id, str) or not self.query_id.strip():
            raise ValueError("query_id must be non-empty")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet intelligence profile query schema_version")
        expected = deterministic_id(
            "wallet_intelligence_profile_query",
            {
                "profile_ids": tuple(item.profile_id for item in self.profiles),
                "schema_version": self.schema_version,
            },
        )
        if self.query_id != expected:
            raise ValueError("query_id does not match result")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "profiles": tuple(item.canonical_dict() for item in self.profiles),
            "query_id": self.query_id,
            "schema_version": self.schema_version,
        }


def query_wallet_intelligence_profiles(
    profiles: tuple[WalletIntelligenceProfile, ...],
    *,
    min_activity_count: int | None = None,
    min_buy_ratio_bps: int | None = None,
    min_completeness_bps: int | None = None,
    min_observed_from_slot: int | None = None,
    max_observed_to_slot: int | None = None,
) -> WalletIntelligenceProfileQueryResult:
    if not isinstance(profiles, tuple) or not all(
        isinstance(item, WalletIntelligenceProfile) for item in profiles
    ):
        raise TypeError("profiles must be a tuple of WalletIntelligenceProfile")
    for name, value in (
        ("min_activity_count", min_activity_count),
        ("min_buy_ratio_bps", min_buy_ratio_bps),
        ("min_completeness_bps", min_completeness_bps),
        ("min_observed_from_slot", min_observed_from_slot),
        ("max_observed_to_slot", max_observed_to_slot),
    ):
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise ValueError(f"{name} must be a non-negative integer")
    if min_buy_ratio_bps is not None and min_buy_ratio_bps > 10000:
        raise ValueError("min_buy_ratio_bps must be at most 10000")
    if min_completeness_bps is not None and min_completeness_bps > 10000:
        raise ValueError("min_completeness_bps must be at most 10000")
    if (
        min_observed_from_slot is not None
        and max_observed_to_slot is not None
        and min_observed_from_slot > max_observed_to_slot
    ):
        raise ValueError("min_observed_from_slot cannot exceed max_observed_to_slot")
    selected = tuple(
        item
        for item in profiles
        if (min_activity_count is None or item.activity_count >= min_activity_count)
        and (
            min_buy_ratio_bps is None
            or (
                item.activity_count > 0
                and item.buy_count * 10000 // item.activity_count >= min_buy_ratio_bps
            )
        )
        and (
            min_completeness_bps is None
            or item.data_completeness_bps >= min_completeness_bps
        )
        and (
            min_observed_from_slot is None
            or item.observed_to_slot >= min_observed_from_slot
        )
        and (
            max_observed_to_slot is None
            or item.observed_from_slot <= max_observed_to_slot
        )
    )
    return WalletIntelligenceProfileQueryResult(
        profiles=selected,
        query_id=deterministic_id(
            "wallet_intelligence_profile_query",
            {
                "profile_ids": tuple(item.profile_id for item in selected),
                "schema_version": _SCHEMA_VERSION,
            },
        ),
    )


__all__ = [
    "WalletIntelligenceProfileQueryResult",
    "query_wallet_intelligence_profiles",
]
