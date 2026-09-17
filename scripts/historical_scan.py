from __future__ import annotations

import argparse
import json
from pathlib import Path

from smart_money.adapters.solana_rpc_fetcher import SolanaRPCFetcher
from smart_money.application.production_shadow import SolanaRPCConfig
from smart_money.application.solana_dex_attribution import (
    extract_swap_candidates,
    inventory_instruction_programs,
    paginate_signatures,
    verify_exact_attribution,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Historical read-only Solana DEX scan")
    parser.add_argument("--wallet", required=True)
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--output", type=Path, default=Path("artifacts/solana/historical_scan.json"))
    parser.add_argument("--checkpoint", type=Path, default=Path("artifacts/solana/historical_scan.checkpoint.json"))
    args = parser.parse_args()
    fetcher = SolanaRPCFetcher(SolanaRPCConfig.from_env())

    def fetch_page(wallet: str, before: str | None):
        response = fetcher.capture_signatures(wallet, args.limit, before)
        return response.get("result", [])

    before = None
    if args.checkpoint.exists():
        checkpoint = json.loads(args.checkpoint.read_text(encoding="utf-8"))
        before = checkpoint.get("before")
    signatures = paginate_signatures(fetch_page, wallet=args.wallet, pages=args.pages, before=before)
    transactions = []
    for row in signatures:
        signature = str(row.get("signature", "")).strip()
        if signature:
            result = fetcher.capture_transaction(signature).get("result")
            if isinstance(result, dict):
                transactions.append(result)
    candidates = extract_swap_candidates(tuple(transactions))
    report = {
        "schema_version": "solana_historical_scan.v1",
        "wallet": args.wallet,
        "signature_count": len(signatures),
        "transaction_count": len(transactions),
        "swap_candidate_count": len(candidates),
        "program_inventory": inventory_instruction_programs(tuple(transactions)),
        "gate": verify_exact_attribution(fixture_count=len(transactions), attributed_count=len(candidates)),
    }
    if signatures:
        args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
        args.checkpoint.write_text(json.dumps({"schema_version": "solana_historical_scan_checkpoint.v1", "wallet": args.wallet, "before": signatures[-1].get("signature")}, sort_keys=True, indent=2), encoding="utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
