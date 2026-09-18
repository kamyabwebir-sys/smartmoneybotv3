from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_cohort_detection import WalletCohort
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_cohort_query.v1"


@dataclass(frozen=True, slots=True)
class WalletCohortQueryResult:
    cohorts: tuple[WalletCohort, ...]
    query_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.cohorts, tuple) or not all(
            isinstance(item, WalletCohort) for item in self.cohorts
        ):
            raise TypeError("cohorts must be a tuple of WalletCohort")
        if not isinstance(self.query_id, str) or not self.query_id.strip():
            raise ValueError("query_id must be non-empty")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet cohort query schema_version")
        expected = deterministic_id(
            "wallet_cohort_query",
            {
                "cohort_ids": tuple(item.cohort_id for item in self.cohorts),
                "schema_version": self.schema_version,
            },
        )
        if self.query_id != expected:
            raise ValueError("query_id does not match result")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "cohorts": tuple(item.canonical_dict() for item in self.cohorts),
            "query_id": self.query_id,
            "schema_version": self.schema_version,
        }


def query_wallet_cohorts(
    cohorts: tuple[WalletCohort, ...],
    *,
    cohort_key: tuple[int, int, int, int] | None = None,
    min_size: int | None = None,
    max_size: int | None = None,
    required_fingerprint_ids: tuple[str, ...] = (),
) -> WalletCohortQueryResult:
    if not isinstance(cohorts, tuple) or not all(
        isinstance(item, WalletCohort) for item in cohorts
    ):
        raise TypeError("cohorts must be a tuple of WalletCohort")
    if cohort_key is not None and (
        not isinstance(cohort_key, tuple)
        or len(cohort_key) != 4
        or not all(isinstance(value, int) and value >= 0 for value in cohort_key)
    ):
        raise ValueError("cohort_key must be a four-item tuple of non-negative integers")
    for name, value in (("min_size", min_size), ("max_size", max_size)):
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 1
        ):
            raise ValueError(f"{name} must be a positive integer")
    if min_size is not None and max_size is not None and min_size > max_size:
        raise ValueError("min_size cannot exceed max_size")
    if not isinstance(required_fingerprint_ids, tuple) or not all(
        isinstance(item, str) and item.strip() for item in required_fingerprint_ids
    ):
        raise TypeError("required_fingerprint_ids must be a tuple of non-empty strings")
    required = frozenset(item.strip() for item in required_fingerprint_ids)
    selected = tuple(
        item
        for item in cohorts
        if (cohort_key is None or item.cohort_key == cohort_key)
        and (min_size is None or len(item.wallets) >= min_size)
        and (max_size is None or len(item.wallets) <= max_size)
        and required.issubset(item.fingerprint_ids)
    )
    return WalletCohortQueryResult(
        cohorts=selected,
        query_id=deterministic_id(
            "wallet_cohort_query",
            {
                "cohort_ids": tuple(item.cohort_id for item in selected),
                "schema_version": _SCHEMA_VERSION,
            },
        ),
    )


__all__ = ["WalletCohortQueryResult", "query_wallet_cohorts"]
