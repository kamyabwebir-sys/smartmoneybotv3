from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.solana_wallet_token_activity import (
    SolanaWalletTokenActivityEvidence,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class SolanaWalletTokenCandidate:
    wallet: str
    mint: str
    activity_count: int
    buy_count: int
    first_slot: int
    last_slot: int
    reasons: tuple[str, ...]
    candidate_id: str
    schema_version: str = "solana_wallet_token_candidate.v1"

    def __post_init__(self) -> None:
        for name in ("wallet", "mint", "candidate_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        for name in ("activity_count", "buy_count", "first_slot", "last_slot"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.buy_count > self.activity_count or self.last_slot < self.first_slot:
            raise ValueError("candidate counters are inconsistent")
        if not isinstance(self.reasons, tuple) or not self.reasons:
            raise ValueError("reasons must be non-empty")
        if not all(isinstance(item, str) and item.strip() for item in self.reasons):
            raise ValueError("reasons must contain non-empty text")
        if self.schema_version != "solana_wallet_token_candidate.v1":
            raise ValueError("unsupported candidate schema_version")
        if self.candidate_id != deterministic_id(
            "solana_wallet_token_candidate", self.identity_payload()
        ):
            raise ValueError("candidate_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "activity_count": self.activity_count,
            "buy_count": self.buy_count,
            "first_slot": self.first_slot,
            "last_slot": self.last_slot,
            "mint": self.mint.strip(),
            "reasons": self.reasons,
            "schema_version": self.schema_version,
            "wallet": self.wallet.strip(),
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"candidate_id": self.candidate_id, **self.identity_payload()}


def discover_solana_wallet_token_candidates(
    ledger: EvidenceLedger,
    *,
    min_buy_count: int = 1,
    min_wallet_activity: int = 1,
) -> tuple[SolanaWalletTokenCandidate, ...]:
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    if isinstance(min_buy_count, bool) or not isinstance(min_buy_count, int) or min_buy_count < 1:
        raise ValueError("min_buy_count must be a positive integer")
    if isinstance(min_wallet_activity, bool) or not isinstance(min_wallet_activity, int) or min_wallet_activity < 1:
        raise ValueError("min_wallet_activity must be a positive integer")
    grouped: dict[tuple[str, str], list[SolanaWalletTokenActivityEvidence]] = {}
    for payload in ledger.iter_payloads():
        if payload.evidence_type != "solana_wallet_token_activity":
            continue
        data = payload.data.get("activity")
        if not hasattr(data, "get"):
            raise ValueError("invalid activity payload in Ledger")
        activity = SolanaWalletTokenActivityEvidence(
            wallet=data["wallet"], mint=data["mint"],
            transaction_signature=data["transaction_signature"], slot=data["slot"],
            direction=data["direction"], token_delta=data["token_delta"],
            native_delta=data["native_delta"], activity_id=data["activity_id"],
            schema_version=data["schema_version"],
        )
        grouped.setdefault((activity.wallet, activity.mint), []).append(activity)
    candidates: list[SolanaWalletTokenCandidate] = []
    for (wallet, mint), activities in sorted(grouped.items()):
        activities.sort(key=lambda item: (item.slot, item.transaction_signature, item.activity_id))
        buys = sum(item.direction == "BUY" for item in activities)
        if len(activities) < min_wallet_activity or buys < min_buy_count:
            continue
        reasons = (
            f"wallet_activity_count={len(activities)}",
            f"buy_count={buys}",
            f"first_slot={activities[0].slot}",
        )
        identity = {
            "activity_count": len(activities), "buy_count": buys,
            "first_slot": activities[0].slot, "last_slot": activities[-1].slot,
            "mint": mint, "reasons": reasons,
            "schema_version": "solana_wallet_token_candidate.v1", "wallet": wallet,
        }
        candidates.append(SolanaWalletTokenCandidate(
            wallet=wallet, mint=mint, activity_count=len(activities), buy_count=buys,
            first_slot=activities[0].slot, last_slot=activities[-1].slot,
            reasons=reasons,
            candidate_id=deterministic_id("solana_wallet_token_candidate", identity),
        ))
    return tuple(candidates)


__all__ = ["SolanaWalletTokenCandidate", "discover_solana_wallet_token_candidates"]
