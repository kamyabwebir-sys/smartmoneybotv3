from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class SolanaTokenBalanceDelta:
    mint: str
    owner: str
    account_index: int
    pre_amount: int
    post_amount: int
    delta: int
    decimals: int
    delta_id: str
    schema_version: str = "solana_token_balance_delta.v1"

    def __post_init__(self) -> None:
        for name in ("mint", "owner", "delta_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        for name in ("account_index", "pre_amount", "post_amount", "delta", "decimals"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
        if min(self.account_index, self.pre_amount, self.post_amount, self.decimals) < 0:
            raise ValueError("balance fields must be non-negative")
        if self.delta != self.post_amount - self.pre_amount:
            raise ValueError("delta does not match balances")
        if self.schema_version != "solana_token_balance_delta.v1":
            raise ValueError("unsupported token balance delta schema_version")
        expected = deterministic_id(
            "solana_token_balance_delta",
            {
                "account_index": self.account_index,
                "decimals": self.decimals,
                "delta": self.delta,
                "mint": self.mint.strip(),
                "owner": self.owner.strip(),
                "post_amount": self.post_amount,
                "pre_amount": self.pre_amount,
                "schema_version": self.schema_version,
            },
        )
        if self.delta_id != expected:
            raise ValueError("delta_id does not match deterministic payload")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "account_index": self.account_index,
            "decimals": self.decimals,
            "delta": self.delta,
            "delta_id": self.delta_id,
            "mint": self.mint.strip(),
            "owner": self.owner.strip(),
            "post_amount": self.post_amount,
            "pre_amount": self.pre_amount,
            "schema_version": self.schema_version,
        }


def extract_solana_token_balance_deltas(raw: dict[str, Any]) -> tuple[SolanaTokenBalanceDelta, ...]:
    if not isinstance(raw, dict):
        raise TypeError("raw transaction must be a dictionary")
    meta = raw.get("meta")
    if not isinstance(meta, dict):
        raise ValueError("raw transaction meta must be a dictionary")
    pre = meta.get("preTokenBalances", [])
    post = meta.get("postTokenBalances", [])
    if not isinstance(pre, list) or not isinstance(post, list):
        raise TypeError("token balances must be lists")

    def index(values: list[dict[str, Any]]) -> dict[tuple[int, str], dict[str, Any]]:
        result: dict[tuple[int, str], dict[str, Any]] = {}
        for item in values:
            if not isinstance(item, dict):
                raise TypeError("token balance entries must be dictionaries")
            account_index = item.get("accountIndex")
            mint = item.get("mint")
            if isinstance(account_index, bool) or not isinstance(account_index, int) or account_index < 0:
                raise ValueError("accountIndex must be non-negative integer")
            if not isinstance(mint, str) or not mint.strip():
                raise ValueError("mint must be non-empty")
            result[(account_index, mint.strip())] = item
        return result

    before, after = index(pre), index(post)
    deltas: list[SolanaTokenBalanceDelta] = []
    for key in sorted(set(before) | set(after)):
        old, new = before.get(key), after.get(key)
        sample = new or old
        amount_old = int((old or {}).get("uiTokenAmount", {}).get("amount", "0"))
        amount_new = int((new or {}).get("uiTokenAmount", {}).get("amount", "0"))
        decimals = int(sample.get("uiTokenAmount", {}).get("decimals", 0))
        owner = str((new or old or {}).get("owner", "unknown"))
        mint = key[1]
        identity = {
            "account_index": key[0], "decimals": decimals, "delta": amount_new - amount_old,
            "mint": mint, "owner": owner, "post_amount": amount_new,
            "pre_amount": amount_old, "schema_version": "solana_token_balance_delta.v1",
        }
        deltas.append(SolanaTokenBalanceDelta(
            mint=mint, owner=owner, account_index=key[0], pre_amount=amount_old,
            post_amount=amount_new, delta=amount_new - amount_old, decimals=decimals,
            delta_id=deterministic_id("solana_token_balance_delta", identity),
        ))
    return tuple(deltas)


__all__ = ["SolanaTokenBalanceDelta", "extract_solana_token_balance_deltas"]
