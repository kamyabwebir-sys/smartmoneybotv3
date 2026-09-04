from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

OPTIONAL_ANALYTICS_PACKAGES = ("networkx", "duckdb", "polars")


def analytics_tool_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for package in OPTIONAL_ANALYTICS_PACKAGES:
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            versions[package] = None
    return versions


__all__ = ["OPTIONAL_ANALYTICS_PACKAGES", "analytics_tool_versions"]
