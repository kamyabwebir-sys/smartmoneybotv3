"""S12.1: strict owner balance evidence, not swap or profit attribution."""

from dataclasses import dataclass
from typing import Any

from smart_money.application.solana_token_balance_delta import extract_solana_token_balance_deltas
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class WalletBalanceReconciliation:
    signature: str
    wallet: str
    native_delta: int
    fee_paid: int
    token_deltas: tuple[tuple[str, int, int], ...]

    @property
    def native_delta_excluding_fee(self) -> int:
        # Still includes rent, account closures and transfers. Not swap spend.
        return self.native_delta + self.fee_paid

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "wallet_balance_reconciliation.v1",
            "signature": self.signature, "wallet": self.wallet,
            "native_delta": self.native_delta, "fee_paid": self.fee_paid,
            "token_deltas": [list(row) for row in self.token_deltas],
        }

    @property
    def evidence_id(self) -> str:
        return deterministic_id("wallet_balance_reconciliation", self.canonical_dict())


def _uint(value: Any) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("expected non-negative integer")
    return value


def reconcile_wallet_balances(raw: dict[str, Any], wallet: str) -> WalletBalanceReconciliation:
    """Accept a resolved RPC transaction result; reject incomplete evidence."""
    if not isinstance(wallet, str) or not wallet or wallet != wallet.strip():
        raise ValueError("wallet must be non-empty canonical text")
    if not isinstance(raw, dict):
        raise ValueError("transaction result required")
    meta = raw.get("meta")
    if not isinstance(meta, dict) or "err" not in meta or meta["err"] is not None:
        raise ValueError("successful transaction metadata required")
    try:
        tx = raw["transaction"]
        signature = tx["signatures"][0]
        keys = [k["pubkey"] if isinstance(k, dict) else k for k in tx["message"]["accountKeys"]]
        pre, post = meta["preBalances"], meta["postBalances"]
    except (KeyError, TypeError, IndexError) as exc:
        raise ValueError("incomplete transaction") from exc
    if not isinstance(signature, str) or not signature.strip():
        raise ValueError("signature required")
    if any(not isinstance(k, str) or not k for k in keys) or len(set(keys)) != len(keys):
        raise ValueError("invalid resolved account keys")
    if wallet not in keys or not isinstance(pre, list) or not isinstance(post, list):
        raise ValueError("wallet balances unavailable")
    if len(pre) != len(keys) or len(post) != len(keys):
        raise ValueError("account keys must resolve all balance indices")
    for amount in pre + post:
        _uint(amount)
    fee = _uint(meta.get("fee"))
    identities: dict[int, tuple[str, str, int]] = {}
    decimals_by_mint: dict[str, int] = {}
    for side in ("preTokenBalances", "postTokenBalances"):
        rows = meta.get(side)
        if not isinstance(rows, list):
            raise ValueError("both token balance arrays required")
        seen: set[int] = set()
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("invalid token balance row")
            index = _uint(row.get("accountIndex"))
            if index >= len(keys) or index in seen:
                raise ValueError("duplicate or out-of-range token account")
            seen.add(index)
            owner, mint, ui = row.get("owner"), row.get("mint"), row.get("uiTokenAmount")
            if any(not isinstance(v, str) or not v or v != v.strip() for v in (owner, mint)):
                raise ValueError("explicit owner and mint required")
            if not isinstance(ui, dict):
                raise ValueError("raw token amount required")
            amount = ui.get("amount")
            if not isinstance(amount, str) or not amount or any(c not in "0123456789" for c in amount):
                raise ValueError("raw token amount must be unsigned decimal text")
            decimals = _uint(ui.get("decimals"))
            if decimals > 255:
                raise ValueError("invalid decimals")
            identity = (owner, mint, decimals)
            if index in identities and identities[index] != identity:
                raise ValueError("token account identity changed")
            if mint in decimals_by_mint and decimals_by_mint[mint] != decimals:
                raise ValueError("mint decimals conflict")
            identities[index] = identity
            decimals_by_mint[mint] = decimals
    totals: dict[tuple[str, int], int] = {}
    for delta in extract_solana_token_balance_deltas(raw):
        if delta.owner == wallet:
            key = (delta.mint, delta.decimals)
            totals[key] = totals.get(key, 0) + delta.delta
    index = keys.index(wallet)
    return WalletBalanceReconciliation(
        signature, wallet, post[index] - pre[index], fee if index == 0 else 0,
        tuple((mint, decimals, amount) for (mint, decimals), amount in sorted(totals.items())),
    )
