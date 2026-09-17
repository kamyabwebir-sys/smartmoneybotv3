#!/usr/bin/env python3
"""
scripts/fetch_live_dex_swaps.py
Direct Solana DEX Swap Harvester for Smart Money System.
Queries canonical DEX programs, filters for successful two-way asset swaps,
and outputs clean fixtures ready for deterministic parser replay.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEX_TARGETS: Dict[str, Dict[str, str]] = {
    "pump_fun": {
        "program_id": "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",
        "label": "Pump.fun Bonding Curve",
    },
    "raydium_v4": {
        "program_id": "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
        "label": "Raydium AMM v4",
    },
    "raydium_cpmm": {
        "program_id": "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C",
        "label": "Raydium CPMM",
    },
    "jupiter_v6": {
        "program_id": "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",
        "label": "Jupiter Aggregator v6",
    },
    "orca_whirlpool": {
        "program_id": "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",
        "label": "Orca Whirlpools",
    },
    "meteora_dlmm": {
        "program_id": "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo",
        "label": "Meteora DLMM",
    },
}

class SolanaRpcClient:
    def __init__(self, rpc_url: str, request_delay: float = 0.5):
        self.rpc_url = rpc_url
        self.request_delay = request_delay

    def call(self, method: str, params: list, max_retries: int = 5) -> Any:
        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": "dex-harvester",
            "method": method,
            "params": params,
        }).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "smartmoneybotv3-dex-harvester/1.0",
        }

        for attempt in range(1, max_retries + 1):
            time.sleep(self.request_delay)
            req = urllib.request.Request(self.rpc_url, data=payload, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=25) as resp:
                    raw = resp.read()
                    data = json.loads(raw.decode("utf-8"))
                    if "error" in data:
                        raise RuntimeError(f"RPC error response: {data['error']}")
                    return data.get("result")
            except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError) as e:
                sleep_time = attempt * 1.5
                if attempt == max_retries:
                    print(f"    [!] Failed RPC {method} after {max_retries} attempts: {e}")
                    raise
                print(f"    [*] RPC transient issue ({e}). Retrying in {sleep_time:.1f}s...")
                time.sleep(sleep_time)

    def get_signatures_for_address(self, address: str, limit: int = 15) -> List[str]:
        res = self.call("getSignaturesForAddress", [address, {"limit": limit, "commitment": "confirmed"}])
        if not isinstance(res, list):
            return []
        sigs = []
        for item in res:
            if isinstance(item, dict) and not item.get("err") and item.get("signature"):
                sigs.append(item["signature"])
        return sigs

    def get_parsed_transaction(self, signature: str) -> Optional[Dict[str, Any]]:
        cfg = {
            "encoding": "jsonParsed",
            "commitment": "confirmed",
            "maxSupportedTransactionVersion": 0,
        }
        return self.call("getTransaction", [signature, cfg])

def extract_account_keys(tx: Dict[str, Any]) -> List[str]:
    keys: List[str] = []
    msg = tx.get("transaction", {}).get("message", {})
    raw_keys = msg.get("accountKeys", [])
    for ak in raw_keys:
        if isinstance(ak, dict) and "pubkey" in ak:
            keys.append(ak["pubkey"])
        elif isinstance(ak, str):
            keys.append(ak)
    meta = tx.get("meta") or {}
    loaded = meta.get("loadedAddresses") or {}
    for extra in loaded.get("writable", []) + loaded.get("readonly", []):
        if extra and extra not in keys:
            keys.append(extra)
    return keys

def classify_swap(tx: Dict[str, Any], venue_hint: str) -> Optional[Dict[str, Any]]:
    meta = tx.get("meta")
    if not meta or meta.get("err") is not None:
        return None

    keys = extract_account_keys(tx)
    if not keys:
        return None

    # Determine wallet (fee payer / primary signer)
    wallet = keys[0]

    pre_balances = meta.get("preBalances", [])
    post_balances = meta.get("postBalances", [])
    sol_delta_lamports = 0
    if len(pre_balances) > 0 and len(post_balances) > 0:
        sol_delta_lamports = post_balances[0] - pre_balances[0]

    fee = meta.get("fee", 0)

    # Token balance deltas for wallet
    pre_tokens = meta.get("preTokenBalances") or []
    post_tokens = meta.get("postTokenBalances") or []

    token_pre_map: Dict[Tuple[str, str], float] = {}
    for tb in pre_tokens:
        owner = tb.get("owner")
        mint = tb.get("mint")
        ui_amt = tb.get("uiTokenAmount", {}).get("uiAmount")
        if owner and mint and ui_amt is not None:
            token_pre_map[(owner, mint)] = float(ui_amt)

    token_post_map: Dict[Tuple[str, str], float] = {}
    for tb in post_tokens:
        owner = tb.get("owner")
        mint = tb.get("mint")
        ui_amt = tb.get("uiTokenAmount", {}).get("uiAmount")
        if owner and mint and ui_amt is not None:
            token_post_map[(owner, mint)] = float(ui_amt)

    deltas_by_mint: Dict[str, float] = {}
    all_pairs = set(token_pre_map.keys()) | set(token_post_map.keys())
    for owner, mint in all_pairs:
        if owner != wallet:
            continue
        pre_val = token_pre_map.get((owner, mint), 0.0)
        post_val = token_post_map.get((owner, mint), 0.0)
        diff = post_val - pre_val
        if abs(diff) > 1e-9:
            deltas_by_mint[mint] = diff

    tokens_gained = [m for m, d in deltas_by_mint.items() if d > 0]
    tokens_spent = [m for m, d in deltas_by_mint.items() if d < 0]

    sol_delta_sol = sol_delta_lamports / 1e9

    direction = "UNKNOWN"
    token_in_mint = None
    token_out_mint = None
    amount_in = None
    amount_out = None

    if sol_delta_sol < -0.0005 and len(tokens_gained) >= 1:
        direction = "BUY"
        token_out_mint = tokens_gained[0]
        amount_out = deltas_by_mint[token_out_mint]
        token_in_mint = "So11111111111111111111111111111111111111112"
        amount_in = abs(sol_delta_sol)
    elif sol_delta_sol > 0.0005 and len(tokens_spent) >= 1:
        direction = "SELL"
        token_in_mint = tokens_spent[0]
        amount_in = abs(deltas_by_mint[token_in_mint])
        token_out_mint = "So11111111111111111111111111111111111111112"
        amount_out = sol_delta_sol
    elif len(tokens_spent) >= 1 and len(tokens_gained) >= 1:
        direction = "SWAP"
        token_in_mint = tokens_spent[0]
        amount_in = abs(deltas_by_mint[token_in_mint])
        token_out_mint = tokens_gained[0]
        amount_out = deltas_by_mint[token_out_mint]

    if direction == "UNKNOWN":
        return None

    fixture = {
        "schema_version": "solana_dex_swap_fixture.v1",
        "signature": tx.get("transaction", {}).get("signatures", [""])[0],
        "slot": tx.get("slot"),
        "block_time": tx.get("blockTime"),
        "wallet": wallet,
        "venue": venue_hint,
        "direction": direction,
        "token_in_mint": token_in_mint,
        "token_out_mint": token_out_mint,
        "amount_in": amount_in,
        "amount_out": amount_out,
        "sol_delta_lamports": sol_delta_lamports,
        "fee_lamports": fee,
        "token_deltas": deltas_by_mint,
        "program_accounts": keys,
        "attribution_complete": True,
        "evidence": "direct_dex_program_harvest",
    }
    return fixture

def main():
    parser = argparse.ArgumentParser(description="Fetch verified live DEX swaps directly from program addresses.")
    parser.add_argument("--limit-per-dex", type=int, default=8, help="Signatures to inspect per DEX")
    parser.add_argument("--max-fixtures-per-dex", type=int, default=3, help="Verified swap fixtures to store per DEX")
    parser.add_argument("--rpc-url", type=str, default=None, help="Custom Solana RPC URL")
    parser.add_argument("--output-dir", type=str, default="fixtures/solana/dex_swaps", help="Output directory for fixtures")
    parser.add_argument("--candidates-file", type=str, default="fixtures/solana/mainnet/verified_dex_candidates.json", help="Candidates bundle path")
    args = parser.parse_args()

    rpc_url = args.rpc_url or os.environ.get("SOLANA_RPC_URL") or "https://api.mainnet-beta.solana.com"
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cand_path = Path(args.candidates_file)
    cand_path.parent.mkdir(parents=True, exist_ok=True)

    client = SolanaRpcClient(rpc_url=rpc_url, request_delay=0.6)
    print(f"[*] Connecting to RPC: {rpc_url}")
    print(f"[*] Target DEXes: {', '.join(DEX_TARGETS.keys())}")

    verified_fixtures: List[Dict[str, Any]] = []
    candidates_list: List[Dict[str, Any]] = []

    for dex_key, dex_meta in DEX_TARGETS.items():
        prog_id = dex_meta["program_id"]
        label = dex_meta["label"]
        print(f"\n[+] Scanning {label} ({prog_id})...")

        try:
            sigs = client.get_signatures_for_address(prog_id, limit=args.limit_per_dex)
        except Exception as e:
            print(f"    [-] Failed fetching signatures for {dex_key}: {e}")
            continue

        print(f"    Found {len(sigs)} recent signatures. Analyzing for swaps...")
        found_for_dex = 0

        for sig in sigs:
            if found_for_dex >= args.max_fixtures_per_dex:
                break
            try:
                tx_data = client.get_parsed_transaction(sig)
                if not tx_data:
                    continue
                fixture = classify_swap(tx_data, venue_hint=dex_key)
                if fixture:
                    verified_fixtures.append(fixture)
                    found_for_dex += 1
                    sig_short = sig[:12]
                    print(f"    [OK] Swapped: {sig_short}... Direction: {fixture['direction']} ({fixture['venue']})")

                    # Write single fixture immediately
                    fpath = out_dir / f"{sig}.json"
                    fpath.write_text(json.dumps(fixture, indent=2), encoding="utf-8")

                    candidates_list.append({
                        "signature": sig,
                        "venue": dex_key,
                        "wallet": fixture["wallet"],
                        "direction": fixture["direction"],
                        "evidence": f"rpc_harvest:{dex_key}",
                    })
            except Exception as ex:
                print(f"    [-] Error processing {sig[:12]}: {ex}")

    # Write candidates bundle for cross-script compatibility
    cand_payload = {
        "jsonrpc": "2.0",
        "result": candidates_list,
    }
    cand_path.write_text(json.dumps(cand_payload, indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"[✓] Harvest Completed: {len(verified_fixtures)} verified DEX fixtures written to {out_dir}")
    print(f"[✓] Candidates bundle written to: {cand_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
