from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from smart_money.application.solana_wallet_token_activity import SolanaWalletTokenActivityEvidence
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "early_entry_consistency.v1"


@dataclass(frozen=True, slots=True)
class EarlyEntryConsistency:
    wallet: str
    evaluated_buy_count: int
    early_entry_count: int
    consistency_bps: int
    token_ids: tuple[str, ...]
    activity_ids: tuple[str, ...]
    consistency_id: str
    schema_version: str = _SCHEMA_VERSION
    observed_from_slot: int | None = None
    observed_to_slot: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.wallet, str) or not self.wallet.strip():
            raise ValueError("wallet must be non-empty")
        for name in ("evaluated_buy_count", "early_entry_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be non-negative integer")
        if self.early_entry_count > self.evaluated_buy_count:
            raise ValueError("early_entry_count cannot exceed evaluated_buy_count")
        if isinstance(self.consistency_bps, bool) or not isinstance(self.consistency_bps, int) or not 0 <= self.consistency_bps <= 10000:
            raise ValueError("consistency_bps must be between 0 and 10000")
        if self.consistency_bps != (self.early_entry_count * 10000 // self.evaluated_buy_count if self.evaluated_buy_count else 0):
            raise ValueError("consistency_bps does not match counts")
        if not isinstance(self.token_ids, tuple) or not isinstance(self.activity_ids, tuple):
            raise TypeError("token_ids and activity_ids must be tuples")
        if len(self.token_ids) != self.evaluated_buy_count or len(self.activity_ids) != self.evaluated_buy_count:
            raise ValueError("identifiers must match evaluated_buy_count")
        if not all(isinstance(item, str) and item.strip() for item in self.token_ids + self.activity_ids):
            raise ValueError("identifiers must be non-empty strings")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported early entry consistency schema_version")
        if (self.observed_from_slot is None) != (self.observed_to_slot is None):
            raise ValueError("slot window must be complete or absent")
        if self.observed_from_slot is not None and (
            isinstance(self.observed_from_slot, bool)
            or not isinstance(self.observed_from_slot, int)
            or self.observed_from_slot < 0
            or isinstance(self.observed_to_slot, bool)
            or not isinstance(self.observed_to_slot, int)
            or self.observed_to_slot < self.observed_from_slot
        ):
            raise ValueError("invalid observed slot window")
        if self.consistency_id != deterministic_id("early_entry_consistency", self.identity_payload()):
            raise ValueError("consistency_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        payload = {
            "activity_ids": self.activity_ids,
            "consistency_bps": self.consistency_bps,
            "early_entry_count": self.early_entry_count,
            "evaluated_buy_count": self.evaluated_buy_count,
            "schema_version": self.schema_version,
            "token_ids": self.token_ids,
            "wallet": self.wallet.strip(),
        }
        if self.observed_from_slot is not None:
            payload["observed_from_slot"] = self.observed_from_slot
            payload["observed_to_slot"] = self.observed_to_slot
        return payload

    def canonical_dict(self) -> dict[str, Any]:
        return {"consistency_id": self.consistency_id, **self.identity_payload()}


def evaluate_early_entry_consistency(
    activities: tuple[SolanaWalletTokenActivityEvidence, ...],
    *,
    reference_slots: Mapping[str, int],
) -> EarlyEntryConsistency:
    if not isinstance(activities, tuple) or not all(
        isinstance(item, SolanaWalletTokenActivityEvidence) for item in activities
    ):
        raise TypeError("activities must be a tuple of SolanaWalletTokenActivityEvidence")
    if not isinstance(reference_slots, Mapping) or not reference_slots:
        raise ValueError("reference_slots must be a non-empty mapping")
    if not all(
        isinstance(key, str) and key.strip()
        and isinstance(value, int) and not isinstance(value, bool) and value >= 0
        for key, value in reference_slots.items()
    ):
        raise ValueError("reference_slots must map token ids to non-negative slots")
    buys = [item for item in activities if item.direction == "BUY" and item.mint in reference_slots]
    buys.sort(key=lambda item: (item.slot, item.transaction_signature, item.activity_id))
    early = sum(item.slot <= reference_slots[item.mint] for item in buys)
    token_ids = tuple(item.mint for item in buys)
    activity_ids = tuple(item.activity_id for item in buys)
    identity = {
        "activity_ids": activity_ids,
        "consistency_bps": early * 10000 // len(buys) if buys else 0,
        "early_entry_count": early,
        "evaluated_buy_count": len(buys),
        "schema_version": _SCHEMA_VERSION,
        "token_ids": token_ids,
        "wallet": activities[0].wallet if activities else "unknown",
        "observed_from_slot": min((item.slot for item in activities), default=None),
        "observed_to_slot": max((item.slot for item in activities), default=None),
    }
    return EarlyEntryConsistency(
        wallet=identity["wallet"],
        evaluated_buy_count=len(buys),
        early_entry_count=early,
        consistency_bps=identity["consistency_bps"],
        token_ids=token_ids,
        activity_ids=activity_ids,
        consistency_id=deterministic_id("early_entry_consistency", identity),
        observed_from_slot=min((item.slot for item in activities), default=None),
        observed_to_slot=max((item.slot for item in activities), default=None),
    )


__all__ = ["EarlyEntryConsistency", "evaluate_early_entry_consistency"]
