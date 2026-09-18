from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.solana_wallet_token_activity import (
    SolanaWalletTokenActivityEvidence,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class SolanaTokenActivityAggregate:
    mint: str
    activity_count: int
    wallet_count: int
    buy_count: int
    sell_count: int
    unknown_count: int
    token_delta_total: int
    native_delta_total: int
    first_slot: int
    last_slot: int
    aggregate_id: str
    schema_version: str = "solana_token_activity_aggregate.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.mint, str) or not self.mint.strip():
            raise ValueError("mint must be non-empty")
        for name in (
            "activity_count",
            "wallet_count",
            "buy_count",
            "sell_count",
            "unknown_count",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        for name in ("token_delta_total", "native_delta_total"):
            if isinstance(getattr(self, name), bool) or not isinstance(getattr(self, name), int):
                raise TypeError(f"{name} must be an integer")
        if self.activity_count != self.buy_count + self.sell_count + self.unknown_count:
            raise ValueError("activity counts do not reconcile")
        if self.wallet_count > self.activity_count:
            raise ValueError("wallet_count cannot exceed activity_count")
        if isinstance(self.first_slot, bool) or not isinstance(self.first_slot, int) or self.first_slot < 0:
            raise ValueError("first_slot must be non-negative")
        if isinstance(self.last_slot, bool) or not isinstance(self.last_slot, int) or self.last_slot < self.first_slot:
            raise ValueError("last_slot must be ordered")
        if self.schema_version != "solana_token_activity_aggregate.v1":
            raise ValueError("unsupported aggregate schema_version")
        if self.aggregate_id != deterministic_id(
            "solana_token_activity_aggregate", self.identity_payload()
        ):
            raise ValueError("aggregate_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "activity_count": self.activity_count,
            "buy_count": self.buy_count,
            "first_slot": self.first_slot,
            "last_slot": self.last_slot,
            "mint": self.mint.strip(),
            "native_delta_total": self.native_delta_total,
            "schema_version": self.schema_version,
            "sell_count": self.sell_count,
            "token_delta_total": self.token_delta_total,
            "unknown_count": self.unknown_count,
            "wallet_count": self.wallet_count,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"aggregate_id": self.aggregate_id, **self.identity_payload()}


def aggregate_solana_token_activity(
    ledger: EvidenceLedger, *, mint: str
) -> SolanaTokenActivityAggregate:
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    if not isinstance(mint, str) or not mint.strip():
        raise ValueError("mint must be non-empty")
    values: list[SolanaWalletTokenActivityEvidence] = []
    for payload in ledger.iter_payloads():
        if payload.evidence_type != "solana_wallet_token_activity":
            continue
        data = payload.data.get("activity")
        if not hasattr(data, "get"):
            raise ValueError("invalid activity payload in Ledger")
        values.append(
            SolanaWalletTokenActivityEvidence(
                wallet=data["wallet"],
                mint=data["mint"],
                transaction_signature=data["transaction_signature"],
                slot=data["slot"],
                direction=data["direction"],
                token_delta=data["token_delta"],
                native_delta=data["native_delta"],
                activity_id=data["activity_id"],
                schema_version=data["schema_version"],
            )
        )
    selected = [item for item in values if item.mint == mint.strip()]
    if not selected:
        raise ValueError("token has no recorded activity")
    selected.sort(key=lambda item: (item.slot, item.transaction_signature, item.activity_id))
    buys = sum(item.direction == "BUY" for item in selected)
    sells = sum(item.direction == "SELL" for item in selected)
    unknown = len(selected) - buys - sells
    wallet_count = len({item.wallet for item in selected})
    identity = {
        "activity_count": len(selected),
        "buy_count": buys,
        "first_slot": selected[0].slot,
        "last_slot": selected[-1].slot,
        "mint": mint.strip(),
        "native_delta_total": sum(item.native_delta for item in selected),
        "schema_version": "solana_token_activity_aggregate.v1",
        "sell_count": sells,
        "token_delta_total": sum(item.token_delta for item in selected),
        "unknown_count": unknown,
        "wallet_count": wallet_count,
    }
    return SolanaTokenActivityAggregate(
        mint=mint,
        activity_count=len(selected),
        wallet_count=wallet_count,
        buy_count=buys,
        sell_count=sells,
        unknown_count=unknown,
        token_delta_total=identity["token_delta_total"],
        native_delta_total=identity["native_delta_total"],
        first_slot=selected[0].slot,
        last_slot=selected[-1].slot,
        aggregate_id=deterministic_id("solana_token_activity_aggregate", identity),
    )


__all__ = ["SolanaTokenActivityAggregate", "aggregate_solana_token_activity"]
