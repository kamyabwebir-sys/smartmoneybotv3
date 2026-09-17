#!/usr/bin/env python3
"""Fetch recent DEX swap transactions from Solana mainnet and emit
minimal structured fixtures (signature/dex/slot/block_time/direction/fee).

Direction detection is signer-centric: only token accounts owned by the
transaction signer (accountKeys[0]) contribute to the mint deltas, so
pool-vault balance changes can never cancel out the user-side legs.
"""

from __future__ import annotations

import argparse
import http.client
import json
import socket
import sys
import time
import urllib.error
import urllib.request
from typing import Any

DEFAULT_RPC_URL = "https://api.mainnet-beta.solana.com"

DEX_PROGRAMS: dict[str, str] = {
    "raydium_amm":     "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
    "raydium_clmm":    "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK",
    "pump_fun":        "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEf6P",
    "orca_whirlpool":  "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3sBMRyCc",
    "orca_token_swap": "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP",
    "jupiter_v6":      "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",
    "serum_v3":        "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin",
}

WSOL = "So11111111111111111111111111111111111111112"

LAMPORTS_PER_SOL = 1_000_000_000
# |SOL delta| below this is treated as rent/ATA noise, not a swap leg.
SOL_DUST_LAMPORTS = 100_000

RETRYABLE_ERRORS = (
    urllib.error.URLError,
    http.client.IncompleteRead,
    http.client.HTTPException,
    socket.timeout,
    TimeoutError,
    ConnectionError,
    json.JSONDecodeError,
)


class RpcError(Exception):
    """Raised when the RPC endpoint returns an error payload."""


def rpc_call(
    url: str,
    method: str,
    params: list[Any],
    *,
    retries: int = 3,
    backoff: float = 1.5,
    timeout: float = 60.0,
) -> Any:
    """JSON-RPC POST with retry/backoff and hardened network error handling."""
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    ).encode("utf-8")
    last_exc: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except RETRYABLE_ERRORS as exc:
            last_exc = exc
            time.sleep(backoff ** attempt)
            continue
        if "error" in body:
            raise RpcError(str(body["error"]))
        return body.get("result")
    raise RpcError(f"RPC failed after {retries} attempts: {last_exc!r}")


def get_signatures(
    url: str, address: str, limit: int, before: str | None = None
) -> list[dict[str, Any]]:
    opts: dict[str, Any] = {"limit": limit, "commitment": "confirmed"}
    if before:
        opts["before"] = before
    result = rpc_call(url, "getSignaturesForAddress", [address, opts])
    return result or []


def get_transaction(url: str, signature: str) -> dict[str, Any] | None:
    """Returns None for pruned transactions (need an archive node)."""
    return rpc_call(
        url,
        "getTransaction",
        [
            signature,
            {
                "encoding": "jsonParsed",
                "maxSupportedTransactionVersion": 0,
                "commitment": "confirmed",
            },
        ],
    )


def _signer(tx: dict[str, Any]) -> str | None:
    """Fee payer / first signer = accountKeys[0] (jsonParsed or raw)."""
    try:
        first = tx["transaction"]["message"]["accountKeys"][0]
    except (KeyError, IndexError, TypeError):
        return None
    if isinstance(first, dict):
        return first.get("pubkey")
    return first if isinstance(first, str) else None


def looks_like_swap(tx: dict[str, Any]) -> str | None:
    """Signer-centric heuristic direction detection.

    Only token accounts owned by the signer contribute to mint deltas
    (no global aggregation -> pool vaults cannot cancel user legs).
    Handles closed token accounts (present in pre, absent in post) and
    native-SOL swaps (pump.fun style) via fee-adjusted pre/postBalances.
    Returns "BUY", "SELL", "SWAP", or None.
    """
    meta = tx.get("meta") or {}
    if meta.get("err") is not None:
        return None
    signer = _signer(tx)
    if not signer:
        return None

    pre = meta.get("preTokenBalances") or []
    post = meta.get("postTokenBalances") or []

    def _amount(bal: dict[str, Any]) -> float:
        return float((bal.get("uiTokenAmount") or {}).get("uiAmount") or 0)

    pre_map: dict[tuple[int, str | None], float] = {}
    post_map: dict[tuple[int, str | None], float] = {}
    for b in pre:
        if b.get("owner") == signer:
            pre_map[(b["accountIndex"], b.get("mint"))] = _amount(b)
    for b in post:
        if b.get("owner") == signer:
            post_map[(b["accountIndex"], b.get("mint"))] = _amount(b)

    deltas: dict[str, float] = {}
    # union of keys => closed accounts (in pre, absent in post) yield -pre_val
    for key in set(pre_map) | set(post_map):
        delta = post_map.get(key, 0.0) - pre_map.get(key, 0.0)
        if delta:
            mint = key[1] or "unknown"
            deltas[mint] = deltas.get(mint, 0.0) + delta

    # Fee-adjusted native SOL delta of the signer (balance index 0).
    sol_delta = 0
    pre_bal = meta.get("preBalances") or []
    post_bal = meta.get("postBalances") or []
    if pre_bal and post_bal:
        fee = meta.get("fee", 0) or 0
        sol_delta = (post_bal[0] - pre_bal[0]) + fee
        if abs(sol_delta) < SOL_DUST_LAMPORTS:
            sol_delta = 0

    positives = [m for m, d in deltas.items() if d > 0]
    negatives = [m for m, d in deltas.items() if d < 0]

    # SPL <-> SPL (incl. WSOL leg)
    if positives and negatives:
        if len(positives) == 1 and len(negatives) == 1:
            gained, lost = positives[0], negatives[0]
            if lost == WSOL:
                return "BUY"
            if gained == WSOL:
                return "SELL"
        return "SWAP"

    # Native SOL leg (pump.fun style): single token leg + SOL moved.
    if len(positives) == 1 and not negatives and sol_delta < 0:
        return "BUY"
    if len(negatives) == 1 and not positives and sol_delta > 0:
        return "SELL"

    return None


def make_fixture(tx: dict[str, Any], sig: str, dex_name: str) -> dict[str, Any]:
    """Build a minimal structured record from a raw transaction."""
    return {
        "signature":    sig,
        "dex":          dex_name,
        "slot":         tx.get("slot"),
        "block_time":   tx.get("blockTime"),
        "direction":    looks_like_swap(tx),
        "fee_lamports": (tx.get("meta") or {}).get("fee", 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch recent DEX swaps and emit structured fixtures."
    )
    parser.add_argument(
        "--dex", choices=sorted(DEX_PROGRAMS), default="raydium_amm"
    )
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--rpc", default=DEFAULT_RPC_URL)
    parser.add_argument("--output", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    address = DEX_PROGRAMS[args.dex]
    if args.dry_run:
        print(f"[dry-run] dex={args.dex} program={address}")
        return 0

    try:
        sigs = get_signatures(args.rpc, address, args.limit)
    except RpcError as exc:
        print(f"[error] getSignaturesForAddress failed: {exc}", file=sys.stderr)
        return 1
    if not sigs:
        print("[warn] no signatures returned", file=sys.stderr)
        return 0

    records: list[dict[str, Any]] = []
    pruned = 0
    for entry in sigs:
        sig = entry.get("signature")
        if not sig:
            continue
        try:
            tx = get_transaction(args.rpc, sig)
        except RpcError as exc:
            print(f"[warn] skip {sig}: {exc}", file=sys.stderr)
            continue
        if tx is None:
            # Pruned on public RPC; needs an archive node to recover.
            pruned += 1
            print(f"[warn] pruned (result null): {sig}", file=sys.stderr)
            continue
        records.append(make_fixture(tx, sig, args.dex))

    if pruned:
        print(
            f"[info] {pruned} pruned tx skipped; use an archive RPC "
            "to recover them.",
            file=sys.stderr,
        )

    out = json.dumps(records, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(out + "\n")
        print(f"[ok] wrote {len(records)} records -> {args.output}")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
