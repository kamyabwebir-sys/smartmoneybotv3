from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.solana_token_balance_delta import (
    SolanaTokenBalanceDelta,
    extract_solana_token_balance_deltas,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class SolanaSwapEvidence:
    transaction_signature: str
    mint: str
    owner: str
    token_delta: int
    native_delta: int
    direction: str
    evidence_id: str
    schema_version: str = "solana_swap_evidence.v1"

    def __post_init__(self) -> None:
        for name in ("transaction_signature", "mint", "owner", "evidence_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        if self.direction not in {"BUY", "SELL", "UNKNOWN"}:
            raise ValueError("unsupported swap direction")
        for name in ("token_delta", "native_delta"):
            if isinstance(getattr(self, name), bool) or not isinstance(getattr(self, name), int):
                raise TypeError(f"{name} must be an integer")
        if self.schema_version != "solana_swap_evidence.v1":
            raise ValueError("unsupported swap evidence schema_version")
        expected = deterministic_id("solana_swap_evidence", self.identity_payload())
        if self.evidence_id != expected:
            raise ValueError("evidence_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "direction": self.direction,
            "mint": self.mint.strip(),
            "native_delta": self.native_delta,
            "owner": self.owner.strip(),
            "schema_version": self.schema_version,
            "token_delta": self.token_delta,
            "transaction_signature": self.transaction_signature.strip(),
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"evidence_id": self.evidence_id, **self.identity_payload()}


def extract_solana_swap_evidence(
    raw: dict[str, Any], *, owner: str, mint: str
) -> SolanaSwapEvidence:
    if not isinstance(owner, str) or not owner.strip():
        raise ValueError("owner must be non-empty")
    if not isinstance(mint, str) or not mint.strip():
        raise ValueError("mint must be non-empty")
    transaction = raw.get("transaction") if isinstance(raw, dict) else None
    signatures = transaction.get("signatures") if isinstance(transaction, dict) else None
    signature = signatures[0] if isinstance(signatures, list) and signatures else None
    if not isinstance(signature, str) or not signature.strip():
        raise ValueError("transaction signature is missing")
    deltas = [
        item for item in extract_solana_token_balance_deltas(raw)
        if item.owner == owner.strip() and item.mint == mint.strip()
    ]
    if len(deltas) != 1:
        raise ValueError("expected exactly one matching token balance delta")
    token_delta: SolanaTokenBalanceDelta = deltas[0]
    meta = raw.get("meta")
    if not isinstance(meta, dict):
        raise ValueError("raw transaction meta must be a dictionary")
    pre = meta.get("preBalances", [])
    post = meta.get("postBalances", [])
    if not isinstance(pre, list) or not isinstance(post, list) or not pre or not post:
        raise ValueError("native balances are missing")
    native_delta = int(post[0]) - int(pre[0])
    if token_delta.delta > 0 and native_delta < 0:
        direction = "BUY"
    elif token_delta.delta < 0 and native_delta > 0:
        direction = "SELL"
    else:
        direction = "UNKNOWN"
    identity = {
        "direction": direction, "mint": mint.strip(), "native_delta": native_delta,
        "owner": owner.strip(), "schema_version": "solana_swap_evidence.v1",
        "token_delta": token_delta.delta, "transaction_signature": signature.strip(),
    }
    return SolanaSwapEvidence(
        transaction_signature=signature, mint=mint, owner=owner,
        token_delta=token_delta.delta, native_delta=native_delta,
        direction=direction, evidence_id=deterministic_id("solana_swap_evidence", identity),
    )


__all__ = ["SolanaSwapEvidence", "extract_solana_swap_evidence"]
