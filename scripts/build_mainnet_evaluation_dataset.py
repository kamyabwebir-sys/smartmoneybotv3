from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.mainnet_evaluation_dataset import (
    build_mainnet_evaluation_dataset,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Join pre-outcome discoveries to later human outcome labels")
    parser.add_argument("--discoveries", type=Path, required=True)
    parser.add_argument("--outcomes", type=Path, required=True)
    parser.add_argument("--training-ids", type=Path)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--horizon", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    discoveries = json.loads(args.discoveries.read_text(encoding="utf-8"))
    outcomes = json.loads(args.outcomes.read_text(encoding="utf-8"))
    training_ids = frozenset(json.loads(args.training_ids.read_text(encoding="utf-8"))) if args.training_ids else frozenset()
    dataset = build_mainnet_evaluation_dataset(discoveries, outcomes, dataset_id=args.dataset_id,
                                               horizon=args.horizon, training_candidate_ids=training_ids)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(dataset, indent=2, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    atomic_replace(temporary, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
