"""Create the non-destructive development directory skeleton.

This helper intentionally does not rewrite source code, tests, governance
documents, or frozen artifacts. Project content is maintained directly in Git.
"""

from __future__ import annotations

import argparse
from pathlib import Path

REQUIRED_DIRECTORIES = (
    "artifacts",
    "docs",
    "fixtures",
    "scripts",
    "src/smart_money/core",
    "src/smart_money/discovery",
    "src/smart_money/ingestion",
    "tests/core",
    "tests/discovery",
    "tests/ingestion",
)


def initialize_project(root: Path) -> tuple[Path, ...]:
    """Create missing project directories and return their resolved paths."""
    resolved_root = root.resolve()
    resolved_root.mkdir(parents=True, exist_ok=True)

    created_or_existing: list[Path] = []
    for relative_path in REQUIRED_DIRECTORIES:
        target = resolved_root / relative_path
        target.mkdir(parents=True, exist_ok=True)
        created_or_existing.append(target)

    return tuple(created_or_existing)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create the smartmoneybotv3 development directory skeleton.",
    )
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="Repository root. Defaults to the current directory.",
    )
    args = parser.parse_args()

    for path in initialize_project(args.root):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
