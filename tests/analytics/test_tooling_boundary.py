from smart_money.analytics.tooling_boundary import OPTIONAL_ANALYTICS_PACKAGES, analytics_tool_versions


def test_analytics_tools_are_optional_and_version_probe_is_safe() -> None:
    assert OPTIONAL_ANALYTICS_PACKAGES == ("networkx", "duckdb", "polars")
    versions = analytics_tool_versions()
    assert set(versions) == set(OPTIONAL_ANALYTICS_PACKAGES)
    assert all(value is None or isinstance(value, str) for value in versions.values())
