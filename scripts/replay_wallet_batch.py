from __future__ import annotations

import argparse
import json
from pathlib import Path

from smart_money.application.solana_candidate_pipeline import (
    build_wallet_profile,
    classify_transaction_programs,
    dashboard_candidate_view,
    discover_token_mints,
    extract_token_balance_deltas,
    infer_direction,
    replay_transaction_batch,
)
from smart_money.ingestion.ledger import EvidenceGroundingLedger


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay captured Solana wallet transactions")
    parser.add_argument("--directory", type=Path, default=Path("fixtures/solana/mainnet"))
    parser.add_argument("--wallet", action="append", required=True)
    args = parser.parse_args()
    paths: list[str] = []
    profiles = []
    all_rows = []
    ledger = EvidenceGroundingLedger()
    for wallet in sorted(set(args.wallet)):
        signature_files = sorted(args.directory.glob(f"{wallet}-tx-*.json"))
        if not signature_files:
            raise FileNotFoundError(f"no transaction fixtures for {wallet}")
        paths.extend(str(path) for path in signature_files)
        activities = []
        for path in signature_files:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            result = data.get("result", {}) if isinstance(data, dict) else {}
            meta = result.get("meta", {}) if isinstance(result, dict) else {}
            deltas = extract_token_balance_deltas(result, wallet)
            for row in deltas:
                all_rows.append(row)
            native = 0
            keys = result.get("transaction", {}).get("message", {}).get("accountKeys", []) if isinstance(result, dict) else []
            for index, key in enumerate(keys):
                address = key.get("pubkey") if isinstance(key, dict) else key
                if str(address).lower() == wallet.lower():
                    pre_lamports = meta.get("preBalances", [])[index] if index < len(meta.get("preBalances", [])) else 0
                    post_lamports = meta.get("postBalances", [])[index] if index < len(meta.get("postBalances", [])) else 0
                    native = int(post_lamports) - int(pre_lamports)
                    break
            token_delta = sum(int(row["delta"]) for row in deltas)
            activities.append({"direction": infer_direction(native, token_delta), "programs": classify_transaction_programs(result), "mints": tuple(row["mint"] for row in deltas), "native_delta": native, "token_delta": token_delta})
        profiles.append(build_wallet_profile(wallet, tuple(activities)))
    replay_transaction_batch(tuple(paths), ledger)
    print(json.dumps({"replayed": len(paths), "ledger_count": ledger.entry_count, "mints": discover_token_mints(tuple(all_rows)), "dashboard": dashboard_candidate_view(tuple(profiles))}, ensure_ascii=False, default=list))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
