from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_candidate_feature.v1"


@dataclass(frozen=True, slots=True)
class WalletCandidateFeature:
    wallet: str
    profile_id: str
    activity_count: int
    buy_ratio_bps: int
    data_completeness_bps: int
    cohort_count: int
    relationship_count: int
    early_entry_consistency_bps: int
    feature_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("wallet", "profile_id", "feature_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        for name in (
            "activity_count",
            "cohort_count",
            "relationship_count",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        for name in (
            "buy_ratio_bps",
            "data_completeness_bps",
            "early_entry_consistency_bps",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 10000:
                raise ValueError(f"{name} must be between 0 and 10000")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet candidate feature schema_version")
        if self.feature_id != deterministic_id(
            "wallet_candidate_feature", self.identity_payload()
        ):
            raise ValueError("feature_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "activity_count": self.activity_count,
            "buy_ratio_bps": self.buy_ratio_bps,
            "cohort_count": self.cohort_count,
            "data_completeness_bps": self.data_completeness_bps,
            "early_entry_consistency_bps": self.early_entry_consistency_bps,
            "profile_id": self.profile_id.strip(),
            "relationship_count": self.relationship_count,
            "schema_version": self.schema_version,
            "wallet": self.wallet.strip(),
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"feature_id": self.feature_id, **self.identity_payload()}


__all__ = ["WalletCandidateFeature"]
