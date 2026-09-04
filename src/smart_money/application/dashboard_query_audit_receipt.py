from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from smart_money.application.dashboard_query_error import DashboardQueryError
from smart_money.application.dashboard_query_result import DashboardQueryResult
from smart_money.core.serialization import canonical_json


@dataclass(frozen=True, slots=True)
class DashboardQueryAuditReceipt:
    """Deterministic audit receipt for one dashboard query execution."""

    query_id: str | None
    status: str
    artifact_id: str
    artifact_kind: str
    output_hash: str
    item_count: int
    schema_versions: tuple[str, ...]
    error_code: str | None = None
    schema_version: str = "dashboard_query_audit_receipt.v1"

    def __post_init__(self) -> None:
        for field_name in (
            "status",
            "artifact_id",
            "artifact_kind",
            "output_hash",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if self.query_id is not None and not isinstance(self.query_id, str):
            raise TypeError("query_id must be a string or None")
        if len(self.output_hash) != 64 or any(
            character not in "0123456789abcdef"
            for character in self.output_hash
        ):
            raise ValueError("output_hash must be lowercase SHA-256 hex")
        if (
            isinstance(self.item_count, bool)
            or not isinstance(self.item_count, int)
            or self.item_count < 0
        ):
            raise ValueError("item_count must be a non-negative integer")
        if not isinstance(self.schema_versions, tuple) or not all(
            isinstance(version, str) and version.strip()
            for version in self.schema_versions
        ):
            raise TypeError("schema_versions must be a tuple of text values")
        if self.error_code is not None and (
            not isinstance(self.error_code, str) or not self.error_code.strip()
        ):
            raise ValueError("error_code must be a non-empty string or None")
        if self.schema_version != "dashboard_query_audit_receipt.v1":
            raise ValueError("unsupported dashboard query audit receipt schema_version")

    @classmethod
    def from_outcome(
        cls,
        outcome: DashboardQueryResult | DashboardQueryError,
    ) -> DashboardQueryAuditReceipt:
        if isinstance(outcome, DashboardQueryResult):
            payload = outcome.canonical_dict()
            return cls(
                query_id=outcome.query.query_id,
                status=outcome.status.value,
                artifact_id=outcome.result_id,
                artifact_kind="result",
                output_hash=_hash(payload),
                item_count=len(outcome.page.items),
                schema_versions=(
                    outcome.query.schema_version,
                    outcome.page.schema_version,
                    outcome.schema_version,
                ),
            )
        if isinstance(outcome, DashboardQueryError):
            payload = outcome.canonical_dict()
            return cls(
                query_id=outcome.query_id,
                status="ERROR",
                artifact_id=outcome.error_id,
                artifact_kind="error",
                output_hash=_hash(payload),
                item_count=0,
                schema_versions=(outcome.schema_version,),
                error_code=outcome.error_code,
            )
        raise TypeError("outcome must be a DashboardQueryResult or DashboardQueryError")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_kind": self.artifact_kind,
            "error_code": self.error_code,
            "item_count": self.item_count,
            "output_hash": self.output_hash,
            "query_id": self.query_id,
            "schema_version": self.schema_version,
            "schema_versions": list(self.schema_versions),
            "status": self.status,
        }

    @property
    def receipt_id(self) -> str:
        return hashlib.sha256(
            canonical_json(self.canonical_dict()).encode("utf-8")
        ).hexdigest()


def _hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


__all__ = ["DashboardQueryAuditReceipt"]
