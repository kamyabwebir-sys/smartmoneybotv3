from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.solana_wallet_token_activity import (
    SolanaWalletTokenActivityEvidence,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class SolanaWalletTokenActivityQueryResult:
    activities: tuple[SolanaWalletTokenActivityEvidence, ...]
    query_id: str
    schema_version: str = "solana_wallet_token_activity_query.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.activities, tuple):
            raise TypeError("activities must be a tuple")
        if not isinstance(self.query_id, str) or not self.query_id.strip():
            raise ValueError("query_id must be non-empty")
        if self.schema_version != "solana_wallet_token_activity_query.v1":
            raise ValueError("unsupported query schema_version")
        expected = deterministic_id(
            "solana_wallet_token_activity_query",
            {"activity_ids": tuple(item.activity_id for item in self.activities), "schema_version": self.schema_version},
        )
        if self.query_id != expected:
            raise ValueError("query_id does not match result")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "activities": tuple(item.canonical_dict() for item in self.activities),
            "query_id": self.query_id,
            "schema_version": self.schema_version,
        }


def query_solana_wallet_token_activity(
    ledger: EvidenceLedger,
    *,
    wallet: str | None = None,
    mint: str | None = None,
    direction: str | None = None,
    min_slot: int | None = None,
    max_slot: int | None = None,
) -> SolanaWalletTokenActivityQueryResult:
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    if direction is not None and direction not in {"BUY", "SELL", "UNKNOWN"}:
        raise ValueError("unsupported direction")
    if min_slot is not None and (isinstance(min_slot, bool) or min_slot < 0):
        raise ValueError("min_slot must be non-negative")
    if max_slot is not None and (isinstance(max_slot, bool) or max_slot < 0):
        raise ValueError("max_slot must be non-negative")
    if min_slot is not None and max_slot is not None and min_slot > max_slot:
        raise ValueError("min_slot cannot exceed max_slot")
    values: list[SolanaWalletTokenActivityEvidence] = []
    for payload in ledger.iter_payloads():
        if payload.evidence_type != "solana_wallet_token_activity":
            continue
        data = payload.data.get("activity")
        if not isinstance(data, Mapping):
            raise ValueError("invalid activity payload in Ledger")
        activity = SolanaWalletTokenActivityEvidence(
            wallet=data["wallet"], mint=data["mint"],
            transaction_signature=data["transaction_signature"], slot=data["slot"],
            direction=data["direction"], token_delta=data["token_delta"],
            native_delta=data["native_delta"], activity_id=data["activity_id"],
            schema_version=data["schema_version"],
        )
        if wallet is not None and activity.wallet != wallet.strip():
            continue
        if mint is not None and activity.mint != mint.strip():
            continue
        if direction is not None and activity.direction != direction:
            continue
        if min_slot is not None and activity.slot < min_slot:
            continue
        if max_slot is not None and activity.slot > max_slot:
            continue
        values.append(activity)
    values.sort(key=lambda item: (item.slot, item.transaction_signature, item.activity_id))
    ids = tuple(item.activity_id for item in values)
    return SolanaWalletTokenActivityQueryResult(
        activities=tuple(values),
        query_id=deterministic_id(
            "solana_wallet_token_activity_query",
            {"activity_ids": ids, "schema_version": "solana_wallet_token_activity_query.v1"},
        ),
    )


__all__ = ["SolanaWalletTokenActivityQueryResult", "query_solana_wallet_token_activity"]
