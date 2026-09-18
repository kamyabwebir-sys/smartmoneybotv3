"""Deprecated compatibility wrapper for scripts.fetch_dex_swaps."""

from __future__ import annotations

import warnings

from scripts.fetch_dex_swaps import main


def deprecated_main() -> int:
    warnings.warn(
        "fetch_dex_swaps_final.py is deprecated; use fetch_dex_swaps.py",
        DeprecationWarning,
        stacklevel=2,
    )
    return main()


if __name__ == "__main__":
    raise SystemExit(deprecated_main())


__all__ = ["deprecated_main"]
