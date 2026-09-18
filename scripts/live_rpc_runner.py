from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path

from smart_money.adapters.persistence.durable_json_ledger import (
    DurableJsonEvidenceLedger,
)
from smart_money.adapters.persistence.live_capture_store import (
    LiveCaptureStore,
    capture_lock,
    write_capture_report,
)
from smart_money.adapters.solana_rpc_fetcher import SolanaRPCFetcher
from smart_money.adapters.solana_signature_ingestion import (
    bind_normalized_signature_batch,
)
from smart_money.application.live_candidate_enrichment import (
    enrich_live_candidates,
    extract_funding_edges,
    materialize_funding_graph_evidence,
)
from smart_money.application.live_route_batch import run_route_checked_batch
from smart_money.application.production_shadow import SolanaRPCConfig


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one live read-only Solana discovery session")
    parser.add_argument("--wallet", required=True)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--enrich-safety-funding", action="store_true")
    parser.add_argument("--mode", choices=("backfill", "head"), default="backfill")
    parser.add_argument("--output", type=Path, default=Path("artifacts/solana/live_session.json"))
    parser.add_argument("--normalized-ledger", type=Path)
    args = parser.parse_args()
    if not 1 <= args.pages <= 100 or not 1 <= args.limit <= 1000:
        parser.error("pages must be 1..100 and limit 1..1000")
    config = SolanaRPCConfig.from_env()
    fetcher = SolanaRPCFetcher(config)
    directory = args.state_dir or args.output.with_suffix(".capture")
    normalized_ledger = DurableJsonEvidenceLedger(
        args.normalized_ledger or directory / "normalized-signatures.json"
    )
    with capture_lock(directory):
        store = LiveCaptureStore(directory, args.wallet, config.network)
        try:
            for _ in range(args.pages):
                if args.mode == "backfill" and store.get("checkpoint")["exhausted"]:
                    result = store.get("latest_report")
                    write_capture_report(args.output, result)
                    break
                result = run_route_checked_batch(
                    lambda wallet, limit, before: store.page(fetcher.capture_signatures, wallet, limit, mode=args.mode),
                    lambda signature: store.transaction(fetcher.capture_transaction, signature),
                    args.wallet, args.limit,
                )
                normalized_receipts = bind_normalized_signature_batch(
                    normalized_ledger,
                    store.transactions_for_pending_page(),
                )
                result["normalized_observations"] = [
                    receipt.canonical_dict() for receipt in normalized_receipts
                ]
                result["normalized_ledger"] = {
                    "content_hash": normalized_ledger.content_hash,
                    "entry_count": normalized_ledger.entry_count,
                }
                if args.enrich_safety_funding:
                    # Prove token-account ownership from the transactions
                    # themselves (meta pre/postTokenBalances carry the ATA,
                    # its owner and mint per accountIndex).
                    token_account_owners: dict[str, str] = {}
                    for response in store.transactions_for_pending_page():
                        try:
                            meta = response["result"]["meta"]
                            keys = response["result"]["transaction"]["message"]["accountKeys"]
                        except (KeyError, TypeError, IndexError):
                            continue
                        for side in ("preTokenBalances", "postTokenBalances"):
                            for row in meta.get(side, ()) or ():
                                if not isinstance(row, Mapping):
                                    continue
                                index, owner = row.get("accountIndex"), row.get("owner")
                                if type(index) is not int or not isinstance(owner, str) or not owner.strip():
                                    continue
                                if not 0 <= index < len(keys):
                                    continue
                                key = keys[index]
                                account = key.get("pubkey") if isinstance(key, Mapping) else key
                                if isinstance(account, str) and account.strip():
                                    token_account_owners[account.strip()] = owner.strip()
                    safety = {}
                    for mint in sorted({row.get("mint") for row in result["ranking"] if isinstance(row.get("mint"), str)}):
                        try:
                            safety[mint] = store.provider_observation("token-safety", mint, fetcher.capture_token_safety)
                        except (OSError, RuntimeError, ValueError):
                            safety[mint] = {"error": "provider_evidence_unavailable"}
                    funding = extract_funding_edges(
                        store.transactions_for_pending_page(),
                        args.wallet,
                        token_account_owners=token_account_owners,
                    )
                    result["ranking"] = enrich_live_candidates(result["ranking"], safety, funding)
                    result["funding_edges"] = list(funding)
                    result["funding_graph_evidence"] = [
                        edge.canonical_dict()
                        for edge in materialize_funding_graph_evidence(funding)
                    ]
                request_count = getattr(fetcher, "request_count", None)
                retry_count = getattr(fetcher, "retry_count", None)
                rate = os.getenv("SOLANA_RPC_COST_PER_MILLION_USD")
                estimated = None
                if rate is not None and type(request_count) is int:
                    estimated = str((Decimal(rate) * request_count / Decimal(1_000_000)).quantize(Decimal("0.00000001")))
                result["operational_metrics"] = {"rpc_request_count": request_count, "rpc_retry_count": retry_count,
                                                 "estimated_rpc_cost_usd": estimated,
                                                 "cost_basis": "configured_rate" if rate is not None else "not_configured"}
                result = store.complete(result)
                write_capture_report(args.output, result)
                if not result["ingestion"]["page_complete"] or result["ingestion"]["exhausted"]:
                    break
        finally:
            store.close()
    print(json.dumps(result, ensure_ascii=False, default=list))
    return 0 if result["ingestion"]["page_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
