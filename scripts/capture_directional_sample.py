"""Bounded read-only discovery; saves raw responses without RPC credentials."""
import json
from pathlib import Path

from smart_money.adapters.solana_rpc_fetcher import SolanaRPCFetcher
from smart_money.application.production_shadow import SolanaRPCConfig
from smart_money.application.fixture_capture import capture_fixture
from smart_money.application.wallet_route_evidence import project_wallet_route
from smart_money.application.verified_swap_legs import verify_swap_legs


def main():
    fetcher = SolanaRPCFetcher(SolanaRPCConfig.from_env())
    pools = ["4MXybVn82rBxjvANiMpmvYUQejRzwkiTnjDT8NQmHMRe", "3RZcRvdU4osDJKDmhCyKqhU5eF8F8Lsy9BDghAM8RmvA"]
    target = Path("fixtures/solana/mainnet/s12-pool-observation.json")
    if not target.exists():
        response = fetcher.request("getMultipleAccounts", [pools, {"encoding": "base64", "commitment": "finalized"}])
        capture_fixture({"addresses": pools, "commitment": "finalized", "response": response}, target)
    out = Path("fixtures/solana/mainnet/s12-directional.json")
    if out.exists():
        print("directional fixture already exists; not overwriting")
        return
    seen = set()
    for pool in pools + ["CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C"]:
        page = fetcher.capture_signatures(pool, 20)
        for entry in page.get("result", []):
            signature = entry["signature"]
            if signature in seen or entry.get("err"):
                continue
            seen.add(signature)
            try:
                payload = fetcher.capture_transaction(signature)
            except RuntimeError:
                print(json.dumps({"status": "rpc_transaction_unavailable", "signature": signature}), flush=True)
                continue
            raw = payload.get("result")
            if not isinstance(raw, dict):
                continue
            try:
                key = raw["transaction"]["message"]["accountKeys"][0]
                wallet = key["pubkey"] if isinstance(key, dict) else key
                route = project_wallet_route(raw, wallet)
                swaps = verify_swap_legs(raw, route)
                if swaps["legs"]:
                    capture_fixture(payload, Path("fixtures/solana/mainnet/s12-search") / (signature + ".json"))
                    print(json.dumps({"legs": len(swaps["legs"]), "gaps": route["gaps"], "flows": [r["classification"] for r in route["items"]]}), flush=True)
                if len(swaps["legs"]) == 1 and not swaps["unresolved"] and not route["gaps"]:
                    leg = swaps["legs"][0]
                    rows = {r["mint"]: r for r in route["items"]}
                    output = rows.get(leg["output_mint"], {})
                    if output.get("classification") == "NET_INFLOW":
                        capture_fixture(payload, out)
                        print(json.dumps({"status": "candidate_captured_not_yet_accepted", "wallet": wallet, "signature": signature, "leg": leg}))
                        return
            except (ValueError, KeyError, TypeError, IndexError) as exc:
                print(json.dumps({"status": "rejected", "reason": str(exc)}), flush=True)
                continue
    print(json.dumps({"status": "no_matching_sample", "transactions_checked": len(seen)}))


if __name__ == "__main__":
    main()
