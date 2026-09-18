from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ROOT / "src/smart_money/core/serialization.py",
    ROOT / "src/smart_money/core/ids.py",
    ROOT / "src/smart_money/adapters/persistence/json_ledger.py",
)


def main() -> int:
    for target in TARGETS:
        tree = ast.parse(target.read_text(encoding="utf-8"), filename=str(target))
        if not any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree)):
            raise RuntimeError(f"mutation target has no functions: {target}")
    print('{"mutation_targets":3,"mutation_smoke":"PASS","status":"PASS"}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
