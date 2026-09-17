"""
Fetch real Solana DEX swap transactions, optionally filtered by wallet address.

Usage examples:
    python fetch_dex_swaps_final.py --dex raydium_amm --limit 20
    python fetch_dex_swaps_final.py --dex jupiter_v6 --wallet <ADDR> --scan-limit 200 --limit 10
    python fetch_dex_swaps_final.py --dex pump_fun --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
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


class RpcError(Exception):
    """Raised when the Solana RPC returns an error payload."""


def rpc_call(
    url: str,
    method: str,
    params: list[Any],
    *,
    retries: int = 3,
    backoff: float = 1.5,
) -> Any:
    """Send a JSON-RPC request and return the ``result`` field."""
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    ).encode()
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read())
            if "error" in body:
                raise RpcError(body["error"])
            return body["result"]
        except (urllib.error.URLError, RpcError) as exc:
            last_exc = exc
            if attempt < retries - 1:
                time.sleep(backoff ** attempt)
    raise RpcError(f"RPC failed after {retries} attempts: {last_exc}") from last_exc


def get_signatures(
    url: str,
    address: str,
    limit: int,
    before: str | None = None,
) -> list[dict[str, Any]]:
    """Return up to *limit* confirmed signatures for *address*."""
    opts: dict[str, Any] = {"limit": limit, "commitment": "confirmed"}
    if before:
        opts["before"] = before
    return rpc_call(url, "getSignaturesForAddress", [address, opts]) or []


def get_transaction(url: str, signature: str) -> dict[str, Any] | None:
    """Fetch a single transaction by signature; returns None on miss."""
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


def tx_involves_wallet(tx: dict[str, Any], wallet: str) -> bool:
    """Return True if *wallet* appears in the transaction account keys."""
    try:
        keys = tx["transaction"]["message"]["accountKeys"]
    except (KeyError, TypeError):
        return False
    for key in keys:
        # jsonParsed encoding returns dicts with a "pubkey" field
        if isinstance(key, dict):
            if key.get("pubkey") == wallet:
                return True
        elif key == wallet:
            return True
    return False


def looks_like_swap(tx: dict[str, Any]) -> str | None:
    """
    Heuristic direction detection from pre/post token balances.

    Returns "BUY", "SELL", "SWAP", or None when the transaction
    does not look like a swap at all.
    """
    try:
        pre = tx["meta"]["preTokenBalances"]
        post = tx["meta"]["postTokenBalances"]
    except (KeyError, TypeError):
        return None

    if not pre or not post:
        return None

    pre_map: dict[tuple[int, str | None], float] = {
        (b["accountIndex"], b.get("mint")): float(
            (b.get("uiTokenAmount") or {}).get("uiAmount") or 0
        )
        for b in pre
    }

    deltas: dict[str, float] = {}
    for b in post:
        key = (b["accountIndex"], b.get("mint"))
        post_val = float((b.get("uiTokenAmount") or {}).get("uiAmount") or 0)
        pre_val = pre_map.get(key, 0.0)
        delta = post_val - pre_val
        if delta:
            mint = b.get("mint") or "unknown"
            deltas[mint] = deltas.get(mint, 0.0) + delta

    positives = [m for m, d in deltas.items() if d > 0]
    negatives = [m for m, d in deltas.items() if d < 0]

    if not positives or not negatives:
        return None

    if len(positives) == 1 and len(negatives) == 1:
        gained, lost = positives[0], negatives[0]
        if lost == WSOL:
            return "BUY"
        if gained == WSOL:
            return "SELL"

    return "SWAP"


def make_fixture(
    tx: dict[str, Any],
    sig: str,
    dex_name: str,
) -> dict[str, Any]:
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
        description="Fetch Solana DEX swap transactions, optionally filtered by wallet.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dex",
        choices=list(DEX_PROGRAMS.keys()),
        default="raydium_amm",
        help="DEX program to query",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of swap records to collect",
    )
    parser.add_argument(
        "--wallet",
        default=None,
        help="Filter to transactions involving this wallet address",
    )
    parser.add_argument(
        "--scan-limit",
        type=int,
        default=100,
        help="Max signatures to scan when --wallet is active (pagination budget)",
    )
    parser.add_argument(
        "--rpc",
        default=DEFAULT_RPC_URL,
        help="Solana RPC endpoint URL",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write results as JSON to this path (omit for stdout)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite --output file if it already exists",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve program address and exit without RPC calls",
    )

    args = parser.parse_args()

    # ── wallet address guard ─────────────────────────────────────
    # Solana public keys are Base58 (no 0 O I l) and 32-44 chars.
    _B58_RE = r"^[1-9A-HJ-NP-Za-km-z]{32,44}$"
    if not re.match(_B58_RE, args.wallet):
        parser.error(
            "--wallet is not a valid Solana Base58 address: "
            f"{args.wallet!r}\n"
            "  (allowed chars 1-9 A-Z a-z, excluding 0 O I l; length 32-44)\n"
            "  Raydium AMM v4 example: "
            "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
        )
    # ─────────────────────────────────────────────────────────────
    address = DEX_PROGRAMS[args.dex]

    if args.dry_run:
        print(f"[dry-run] {args.dex} -> {address}")
        if args.wallet:
            print(f"[dry-run] wallet filter: {args.wallet}")
        return 0

    # Refuse to silently clobber an existing output file
    if args.output and args.output.exists() and not args.overwrite:
        print(
            f"[error] {args.output} already exists; pass --overwrite to replace it",
            file=sys.stderr,
        )
        return 1

    print(
        f"[info] querying {args.dex} ({address}) limit={args.limit}",
        file=sys.stderr,
    )
    if args.wallet:
        print(
            f"[info] wallet filter={args.wallet}  scan-limit={args.scan_limit}",
            file=sys.stderr,
        )

    records: list[dict[str, Any]] = []
    before: str | None = None
    # Without wallet filtering we only need `limit` signatures total.
    # With filtering, we may need to scan many more to find `limit` matches.
    scan_budget: int = args.scan_limit if args.wallet else args.limit

    while len(records) < args.limit and scan_budget > 0:
        fetch_n = min(scan_budget, 1000)  # Solana RPC hard cap per call
        sigs = get_signatures(args.rpc, address, fetch_n, before)
        if not sigs:
            break

        for entry in sigs:
            if len(records) >= args.limit:
                break
            sig = entry["signature"]
            try:
                tx = get_transaction(args.rpc, sig)
            except RpcError as exc:
                print(f"[warn] skipping {sig[:12]}...: {exc}", file=sys.stderr)
                continue
            if tx is None:
                continue
            if args.wallet and not tx_involves_wallet(tx, args.wallet):
                continue
            records.append(make_fixture(tx, sig, args.dex))

        scan_budget -= len(sigs)
        if len(sigs) < fetch_n:
            break  # no more history to page through
        _last = sigs[-1]
        _cursor = _last.get("signature") if isinstance(_last, dict) else None
        if not _cursor or len(_cursor) < 80:
            break  # invalid cursor – abort pagination to prevent WrongSize RPC error
        before = _cursor

    if args.wallet and len(records) < args.limit:
        print(
            f"[warn] only {len(records)}/{args.limit} records found within "
            f"scan-limit={args.scan_limit}; increase --scan-limit to search further",
            file=sys.stderr,
        )

    # ── output ──────────────────────────────────────────────────────────
    payload = json.dumps(records, indent=2)
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
        print(
            f"[info] wrote {len(records)} records -> {args.output}",
            file=sys.stderr,
        )
    else:
        print(payload)

    return 0


raise SystemExit(main())
