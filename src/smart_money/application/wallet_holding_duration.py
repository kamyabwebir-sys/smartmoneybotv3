"""Replayable FIFO holding-duration evidence measured in Solana slots."""

from __future__ import annotations

from dataclasses import dataclass

from smart_money.application.solana_wallet_token_activity import (
    SolanaWalletTokenActivityEvidence,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class WalletHoldingDurationProfile:
    wallet: str
    closed_lot_count: int
    open_lot_count: int
    total_held_slots: int
    mean_held_slots: int
    minimum_held_slots: int | None
    maximum_held_slots: int | None
    activity_ids: tuple[str, ...]
    profile_id: str
    schema_version: str = "wallet_holding_duration.v1"

    def __post_init__(self) -> None:
        for name in (
            "closed_lot_count",
            "open_lot_count",
            "total_held_slots",
            "mean_held_slots",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if (self.minimum_held_slots is None) != (self.maximum_held_slots is None):
            raise ValueError("holding duration bounds must be both present or absent")
        if self.minimum_held_slots is not None and not (
            0 <= self.minimum_held_slots <= self.maximum_held_slots
        ):
            raise ValueError("holding duration bounds are invalid")
        if self.closed_lot_count == 0 and (
            self.total_held_slots != 0
            or self.mean_held_slots != 0
            or self.minimum_held_slots is not None
        ):
            raise ValueError("empty closed-lot profile must contain zero duration")
        if self.closed_lot_count and self.mean_held_slots != (
            self.total_held_slots // self.closed_lot_count
        ):
            raise ValueError("mean_held_slots does not reconcile")
        if self.profile_id != deterministic_id(
            "wallet-holding-duration", self.identity_payload()
        ):
            raise ValueError("profile_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, object]:
        return {
            "activity_ids": self.activity_ids,
            "closed_lot_count": self.closed_lot_count,
            "maximum_held_slots": self.maximum_held_slots,
            "mean_held_slots": self.mean_held_slots,
            "minimum_held_slots": self.minimum_held_slots,
            "open_lot_count": self.open_lot_count,
            "schema_version": self.schema_version,
            "total_held_slots": self.total_held_slots,
            "wallet": self.wallet,
        }

    def canonical_dict(self) -> dict[str, object]:
        return {"profile_id": self.profile_id, **self.identity_payload()}


def build_wallet_holding_duration_profile(
    activities: tuple[SolanaWalletTokenActivityEvidence, ...],
) -> WalletHoldingDurationProfile:
    if not activities or not all(
        isinstance(item, SolanaWalletTokenActivityEvidence) for item in activities
    ):
        raise TypeError("activities must be a non-empty tuple")
    wallet = activities[0].wallet
    if any(item.wallet != wallet for item in activities):
        raise ValueError("activities must share one wallet")
    ordered = tuple(
        sorted(
            activities,
            key=lambda item: (item.slot, item.transaction_signature, item.activity_id),
        )
    )
    lots: dict[str, list[list[int]]] = {}
    durations: list[int] = []
    for item in ordered:
        if item.direction == "BUY" and item.token_delta > 0:
            lots.setdefault(item.mint, []).append([item.token_delta, item.slot])
            continue
        if item.direction != "SELL" or item.token_delta >= 0:
            continue
        remaining = -item.token_delta
        queue = lots.setdefault(item.mint, [])
        while remaining and queue:
            amount, opened_slot = queue[0]
            consumed = min(amount, remaining)
            if consumed > 0:
                durations.append(item.slot - opened_slot)
            amount -= consumed
            remaining -= consumed
            if amount:
                queue[0][0] = amount
            else:
                queue.pop(0)
    open_count = sum(len(queue) for queue in lots.values())
    total = sum(durations)
    identity = {
        "activity_ids": tuple(item.activity_id for item in ordered),
        "closed_lot_count": len(durations),
        "maximum_held_slots": max(durations) if durations else None,
        "mean_held_slots": total // len(durations) if durations else 0,
        "minimum_held_slots": min(durations) if durations else None,
        "open_lot_count": open_count,
        "schema_version": "wallet_holding_duration.v1",
        "total_held_slots": total,
        "wallet": wallet,
    }
    return WalletHoldingDurationProfile(
        profile_id=deterministic_id("wallet-holding-duration", identity),
        **identity,
    )


__all__ = [
    "WalletHoldingDurationProfile",
    "build_wallet_holding_duration_profile",
]
