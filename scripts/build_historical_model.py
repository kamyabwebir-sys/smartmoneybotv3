from __future__ import annotations

import argparse
import json
from pathlib import Path

from smart_money.application.historical_runtime import HistoricalJsonStore
from smart_money.application.solana_dex_attribution import (
    build_dex_evidence_dashboard,
    build_historical_candidate_read_model,
    project_historical_scan,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build read-only historical model from Solana fixtures")
    parser.add_argument("--directory", type=Path, default=Path("fixtures/solana/mainnet"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/solana/historical_model.json"))
    args = parser.parse_args()
    results = []
    for path in sorted(args.directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        result = data.get("result") if isinstance(data, dict) else None
        if isinstance(result, dict):
            results.append(result)
    scan = project_historical_scan(tuple(results))
    model = {"schema_version": "solana_historical_model.v1", "scan": scan, "candidates": build_historical_candidate_read_model(()), "dex": build_dex_evidence_dashboard(())}
    HistoricalJsonStore(args.output).save(model)
    print(json.dumps({"status": "built", "path": str(args.output), "transaction_count": len(results)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
