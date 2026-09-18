from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from smart_money.adapters.persistence.durable_json_ledger import (
    DurableJsonEvidenceLedger,
)
from smart_money.adapters.persistence.live_capture_store import write_capture_report
from smart_money.adapters.solana_dex_fetcher import (
    DEX_PROGRAMS,
    DexFetchOptions,
    fetch_dex_swaps,
)
from smart_money.adapters.solana_rpc_fetcher import SolanaRPCFetcher
from smart_money.application.production_shadow import SolanaRPCConfig


def parse_options(argv: list[str] | None = None) -> tuple[argparse.Namespace, DexFetchOptions]:
    parser = argparse.ArgumentParser(description="Fetch signer-centric Solana DEX swaps")
    parser.add_argument("--dex", choices=sorted(DEX_PROGRAMS), default="raydium_amm")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--scan-limit", type=int, default=100)
    parser.add_argument("--wallet")
    parser.add_argument("--output", type=Path, default=Path("artifacts/solana/dex-swaps.json"))
    parser.add_argument("--ledger", type=Path, default=Path("artifacts/solana/dex-swaps.ledger.json"))
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        options = DexFetchOptions(args.dex, args.limit, args.scan_limit, args.wallet)
    except ValueError as exc:
        parser.error(str(exc))
    return args, options


def main(argv: list[str] | None = None) -> int:
    args, options = parse_options(argv)
    if args.dry_run:
        print(json.dumps({"dex": options.dex, "program": DEX_PROGRAMS[options.dex], "wallet": options.wallet}, sort_keys=True))
        return 0
    if args.output.exists() and not args.overwrite:
        print(f"[error] {args.output} exists; use --overwrite", file=sys.stderr)
        return 2
    fetcher = SolanaRPCFetcher(SolanaRPCConfig.from_env())
    ledger = DurableJsonEvidenceLedger(args.ledger)
    report = fetch_dex_swaps(fetcher, options, ledger=ledger)
    document = report.canonical_dict()
    write_capture_report(args.output, document)
    print(json.dumps(document, ensure_ascii=False, default=list))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
