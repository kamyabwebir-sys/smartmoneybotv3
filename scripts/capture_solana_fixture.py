from __future__ import annotations

import argparse
import json
from pathlib import Path

from smart_money.adapters.solana_rpc_fetcher import SolanaRPCFetcher
from smart_money.application.fixture_capture import capture_fixture
from smart_money.application.production_shadow import SolanaRPCConfig


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture one read-only Solana RPC fixture")
    parser.add_argument("method", choices=("getSlot", "getBlockHeight", "getSignaturesForAddress", "getTransaction"))
    parser.add_argument("value", nargs="?")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fetcher = SolanaRPCFetcher(SolanaRPCConfig.from_env())
    if args.method == "getSignaturesForAddress":
        if not args.value:
            parser.error("getSignaturesForAddress requires an address")
        response = fetcher.capture_signatures(args.value)
    elif args.method == "getTransaction":
        if not args.value:
            parser.error("getTransaction requires a signature")
        response = fetcher.capture_transaction(args.value)
    else:
        response = fetcher.request(args.method)
    capture_fixture(response, args.output)
    print(json.dumps({"status": "captured", "path": str(args.output), "method": args.method}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
