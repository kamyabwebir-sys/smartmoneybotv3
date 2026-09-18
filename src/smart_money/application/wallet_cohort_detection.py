from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_behavior_fingerprint import WalletBehaviorFingerprint
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_cohort_detection.v1"


@dataclass(frozen=True, slots=True)
class WalletCohort:
    cohort_key: tuple[int, int, int, int]
    fingerprint_ids: tuple[str, ...]
    wallets: tuple[str, ...]
    cohort_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.cohort_key, tuple) or len(self.cohort_key) != 4:
            raise TypeError("cohort_key must be a four-item tuple")
        if not all(isinstance(value, int) and value >= 0 for value in self.cohort_key):
            raise ValueError("cohort_key values must be non-negative integers")
        if not isinstance(self.fingerprint_ids, tuple) or not self.fingerprint_ids:
            raise ValueError("fingerprint_ids must be non-empty tuple")
        if not isinstance(self.wallets, tuple) or not self.wallets:
            raise ValueError("wallets must be non-empty tuple")
        if len(self.fingerprint_ids) != len(self.wallets):
            raise ValueError("fingerprint_ids and wallets must have equal length")
        if len(set(self.fingerprint_ids)) != len(self.fingerprint_ids):
            raise ValueError("fingerprint_ids must be unique")
        if len(set(self.wallets)) != len(self.wallets):
            raise ValueError("wallets must be unique")
        if not all(isinstance(value, str) and value.strip() for value in self.fingerprint_ids + self.wallets):
            raise ValueError("cohort identifiers must be non-empty strings")
        if not isinstance(self.cohort_id, str) or not self.cohort_id.strip():
            raise ValueError("cohort_id must be non-empty")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet cohort schema_version")
        if self.cohort_id != deterministic_id("wallet_cohort", self.identity_payload()):
            raise ValueError("cohort_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "cohort_key": self.cohort_key,
            "fingerprint_ids": self.fingerprint_ids,
            "schema_version": self.schema_version,
            "wallets": self.wallets,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"cohort_id": self.cohort_id, **self.identity_payload()}


def detect_wallet_cohorts(
    fingerprints: tuple[WalletBehaviorFingerprint, ...],
    *,
    bucket_size_bps: int = 1000,
) -> tuple[WalletCohort, ...]:
    if not isinstance(fingerprints, tuple) or not all(
        isinstance(item, WalletBehaviorFingerprint) for item in fingerprints
    ):
        raise TypeError("fingerprints must be a tuple of WalletBehaviorFingerprint")
    if isinstance(bucket_size_bps, bool) or not isinstance(bucket_size_bps, int) or not 1 <= bucket_size_bps <= 10000:
        raise ValueError("bucket_size_bps must be between 1 and 10000")
    grouped: dict[tuple[int, int, int, int], list[WalletBehaviorFingerprint]] = {}
    for fingerprint in fingerprints:
        key = (
            fingerprint.buy_ratio_bps // bucket_size_bps,
            fingerprint.sell_ratio_bps // bucket_size_bps,
            fingerprint.token_observation_ratio_bps // bucket_size_bps,
            fingerprint.data_completeness_bps // bucket_size_bps,
        )
        grouped.setdefault(key, []).append(fingerprint)
    cohorts: list[WalletCohort] = []
    for key, values in grouped.items():
        values.sort(key=lambda item: (item.wallet, item.fingerprint_id))
        fingerprint_ids = tuple(item.fingerprint_id for item in values)
        wallets = tuple(item.wallet for item in values)
        identity = {
            "cohort_key": key,
            "fingerprint_ids": fingerprint_ids,
            "schema_version": _SCHEMA_VERSION,
            "wallets": wallets,
        }
        cohorts.append(
            WalletCohort(
                cohort_key=key,
                fingerprint_ids=fingerprint_ids,
                wallets=wallets,
                cohort_id=deterministic_id("wallet_cohort", identity),
            )
        )
    return tuple(sorted(cohorts, key=lambda item: item.cohort_id))


__all__ = ["WalletCohort", "detect_wallet_cohorts"]
