from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.early_entry_consistency import EarlyEntryConsistency
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "early_entry_consistency_query.v1"


@dataclass(frozen=True, slots=True)
class EarlyEntryConsistencyQueryResult:
    matches: tuple[EarlyEntryConsistency, ...]
    query_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.matches, tuple) or not all(
            isinstance(item, EarlyEntryConsistency) for item in self.matches
        ):
            raise TypeError("matches must be a tuple of EarlyEntryConsistency")
        if not isinstance(self.query_id, str) or not self.query_id.strip():
            raise ValueError("query_id must be non-empty")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported early entry consistency query schema_version")
        expected = deterministic_id(
            "early_entry_consistency_query",
            {
                "consistency_ids": tuple(item.consistency_id for item in self.matches),
                "schema_version": self.schema_version,
            },
        )
        if self.query_id != expected:
            raise ValueError("query_id does not match result")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "matches": tuple(item.canonical_dict() for item in self.matches),
            "query_id": self.query_id,
            "schema_version": self.schema_version,
        }


def query_early_entry_consistency(
    values: tuple[EarlyEntryConsistency, ...],
    *,
    min_consistency_bps: int | None = None,
    min_samples: int | None = None,
    min_observed_slot: int | None = None,
    max_observed_slot: int | None = None,
) -> EarlyEntryConsistencyQueryResult:
    if not isinstance(values, tuple) or not all(
        isinstance(item, EarlyEntryConsistency) for item in values
    ):
        raise TypeError("values must be a tuple of EarlyEntryConsistency")
    for name, value in (
        ("min_consistency_bps", min_consistency_bps),
        ("min_samples", min_samples),
        ("min_observed_slot", min_observed_slot),
        ("max_observed_slot", max_observed_slot),
    ):
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise ValueError(f"{name} must be a non-negative integer")
    if min_consistency_bps is not None and min_consistency_bps > 10000:
        raise ValueError("min_consistency_bps must be at most 10000")
    if min_observed_slot is not None and max_observed_slot is not None and min_observed_slot > max_observed_slot:
        raise ValueError("min_observed_slot cannot exceed max_observed_slot")
    selected = tuple(
        item
        for item in values
        if (min_consistency_bps is None or item.consistency_bps >= min_consistency_bps)
        and (min_samples is None or item.evaluated_buy_count >= min_samples)
        and (
            min_observed_slot is None
            or (
                item.observed_to_slot is not None
                and item.observed_to_slot >= min_observed_slot
            )
        )
        and (
            max_observed_slot is None
            or (
                item.observed_from_slot is not None
                and item.observed_from_slot <= max_observed_slot
            )
        )
    )
    return EarlyEntryConsistencyQueryResult(
        matches=selected,
        query_id=deterministic_id(
            "early_entry_consistency_query",
            {
                "consistency_ids": tuple(item.consistency_id for item in selected),
                "schema_version": _SCHEMA_VERSION,
            },
        ),
    )


__all__ = ["EarlyEntryConsistencyQueryResult", "query_early_entry_consistency"]
