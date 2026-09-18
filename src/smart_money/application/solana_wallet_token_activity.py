from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.core.ids import deterministic_id
from smart_money.domain.solana_observation import SolanaChainObservation
from smart_money.application.solana_swap_evidence import SolanaSwapEvidence


@dataclass(frozen=True, slots=True)
class SolanaWalletTokenActivityEvidence:
    wallet: str
    mint: str
    transaction_signature: str
    slot: int
    direction: str
    token_delta: int
    native_delta: int
    activity_id: str
    schema_version: str = "solana_wallet_token_activity.v1"

    def __post_init__(self) -> None:
        for name in ("wallet", "mint", "transaction_signature", "activity_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        if isinstance(self.slot, bool) or not isinstance(self.slot, int) or self.slot < 0:
            raise ValueError("slot must be a non-negative integer")
        for name in ("token_delta", "native_delta"):
            if isinstance(getattr(self, name), bool) or not isinstance(getattr(self, name), int):
                raise TypeError(f"{name} must be an integer")
        if self.direction not in {"BUY", "SELL", "UNKNOWN"}:
            raise ValueError("unsupported activity direction")
        if self.schema_version != "solana_wallet_token_activity.v1":
            raise ValueError("unsupported activity schema_version")
        if self.activity_id != deterministic_id(
            "solana_wallet_token_activity", self.identity_payload()
        ):
            raise ValueError("activity_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "direction": self.direction,
            "mint": self.mint.strip(),
            "native_delta": self.native_delta,
            "schema_version": self.schema_version,
            "slot": self.slot,
            "token_delta": self.token_delta,
            "transaction_signature": self.transaction_signature.strip(),
            "wallet": self.wallet.strip(),
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"activity_id": self.activity_id, **self.identity_payload()}


def build_solana_wallet_token_activity(
    observation: SolanaChainObservation,
    swap: SolanaSwapEvidence,
) -> SolanaWalletTokenActivityEvidence:
    if not isinstance(observation, SolanaChainObservation):
        raise TypeError("observation must be a SolanaChainObservation")
    if not isinstance(swap, SolanaSwapEvidence):
        raise TypeError("swap must be SolanaSwapEvidence")
    if observation.transaction_signature != swap.transaction_signature:
        raise ValueError("observation and swap signature mismatch")
    identity = {
        "direction": swap.direction,
        "mint": swap.mint,
        "native_delta": swap.native_delta,
        "schema_version": "solana_wallet_token_activity.v1",
        "slot": observation.slot,
        "token_delta": swap.token_delta,
        "transaction_signature": observation.transaction_signature,
        "wallet": swap.owner,
    }
    return SolanaWalletTokenActivityEvidence(
        wallet=swap.owner,
        mint=swap.mint,
        transaction_signature=observation.transaction_signature,
        slot=observation.slot,
        direction=swap.direction,
        token_delta=swap.token_delta,
        native_delta=swap.native_delta,
        activity_id=deterministic_id("solana_wallet_token_activity", identity),
    )


__all__ = [
    "SolanaWalletTokenActivityEvidence",
    "build_solana_wallet_token_activity",
]
