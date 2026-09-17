from __future__ import annotations

import argparse
import json
from pathlib import Path

from smart_money.application.independent_quality_evaluation import (
    evaluate_independent_dataset,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate candidate quality on a held-out corpus")
    parser.add_argument("dataset", type=Path)
    args = parser.parse_args()
    document = json.loads(args.dataset.read_text(encoding="utf-8"))
    print(json.dumps(evaluate_independent_dataset(document).canonical_dict(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
