from __future__ import annotations

from types import MappingProxyType

import pytest

from smart_money.application.audit_receipt_schema_registry import (
    registered_schema_versions,
    schema_version,
    validate_schema_version,
)


def test_registry_returns_immutable_known_schema_versions() -> None:
    versions = registered_schema_versions()
    assert isinstance(versions, MappingProxyType)
    assert schema_version("commit_receipt_verification") == "commit_receipt_verification.v1"
    assert validate_schema_version(
        "commit_receipt_audit", "commit_receipt_audit.v1"
    ) == "commit_receipt_audit.v1"
    with pytest.raises(TypeError):
        versions["new"] = "new.v1"  # type: ignore[index]


def test_registry_fails_closed_on_unknown_or_mismatched_schema() -> None:
    with pytest.raises(ValueError, match="unknown audit receipt schema"):
        schema_version("unknown")
    with pytest.raises(ValueError, match="unsupported"):
        validate_schema_version("commit_receipt_audit", "commit_receipt_audit.v2")
