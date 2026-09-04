from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_intelligence_profile import WalletIntelligenceProfile
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_behavior_fingerprint.v1"


@dataclass(frozen=True, slots=True)
class WalletBehaviorFingerprint:
    wallet: str
    profile_id: str
    buy_ratio_bps: int
    sell_ratio_bps: int
    unknown_ratio_bps: int
    activity_per_observation: int
    token_observation_ratio_bps: int
    data_completeness_bps: int
    fingerprint_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.wallet, str) or not self.wallet.strip():
            raise ValueError("wallet must be non-empty")
        if not isinstance(self.profile_id, str) or not self.profile_id.strip():
            raise ValueError("profile_id must be non-empty")
        for name in (
            "buy_ratio_bps", "sell_ratio_bps", "unknown_ratio_bps",
            "token_observation_ratio_bps", "data_completeness_bps",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 10000:
                raise ValueError(f"{name} must be between 0 and 10000")
        if isinstance(self.activity_per_observation, bool) or not isinstance(self.activity_per_observation, int) or self.activity_per_observation < 0:
            raise ValueError("activity_per_observation must be non-negative integer")
        if self.buy_ratio_bps + self.sell_ratio_bps + self.unknown_ratio_bps != 10000:
            raise ValueError("behavior ratios must reconcile to 10000")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet behavior fingerprint schema_version")
        if self.fingerprint_id != deterministic_id(
            "wallet_behavior_fingerprint", self.identity_payload()
        ):
            raise ValueError("fingerprint_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "activity_per_observation": self.activity_per_observation,
            "buy_ratio_bps": self.buy_ratio_bps,
            "data_completeness_bps": self.data_completeness_bps,
            "profile_id": self.profile_id,
            "schema_version": self.schema_version,
            "sell_ratio_bps": self.sell_ratio_bps,
            "token_observation_ratio_bps": self.token_observation_ratio_bps,
            "unknown_ratio_bps": self.unknown_ratio_bps,
            "wallet": self.wallet.strip(),
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"fingerprint_id": self.fingerprint_id, **self.identity_payload()}


def project_wallet_behavior_fingerprint(
    profile: WalletIntelligenceProfile,
) -> WalletBehaviorFingerprint:
    if not isinstance(profile, WalletIntelligenceProfile):
        raise TypeError("profile must be WalletIntelligenceProfile")
    total = profile.activity_count
    buy = profile.buy_count * 10000 // total if total else 0
    sell = profile.sell_count * 10000 // total if total else 0
    unknown = 10000 - buy - sell if total else 10000
    activity_per_observation = profile.activity_count // profile.observation_count
    token_ratio = (
        min(10000, profile.distinct_token_observation_total * 10000 // profile.activity_count)
        if total else 0
    )
    identity = {
        "activity_per_observation": activity_per_observation,
        "buy_ratio_bps": buy,
        "data_completeness_bps": profile.data_completeness_bps,
        "profile_id": profile.profile_id,
        "schema_version": _SCHEMA_VERSION,
        "sell_ratio_bps": sell,
        "token_observation_ratio_bps": token_ratio,
        "unknown_ratio_bps": unknown,
        "wallet": profile.wallet.strip(),
    }
    return WalletBehaviorFingerprint(
        fingerprint_id=deterministic_id("wallet_behavior_fingerprint", identity),
        **identity,
    )


__all__ = ["WalletBehaviorFingerprint", "project_wallet_behavior_fingerprint"]
