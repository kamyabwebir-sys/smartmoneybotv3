from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from smart_money.application.wallet_relationship_intelligence_query import (
    WalletRelationshipIntelligenceQueryResult,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_relationship_intelligence_query_audit.v1"


@dataclass(frozen=True, slots=True)
class WalletRelationshipIntelligenceQueryAuditReceipt:
    query_id: str
    result_count: int
    parameters: Mapping[str, str]
    audit_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("query_id", "audit_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if isinstance(self.result_count, bool) or not isinstance(self.result_count, int) or self.result_count < 0:
            raise ValueError("result_count must be a non-negative integer")
        if not isinstance(self.parameters, Mapping):
            raise TypeError("parameters must be a mapping")
        if not all(
            isinstance(key, str) and key.strip()
            and isinstance(value, str)
            for key, value in self.parameters.items()
        ):
            raise ValueError("parameters must contain text keys and values")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet relationship query audit schema_version")
        if self.audit_id != deterministic_id(
            "wallet_relationship_intelligence_query_audit", self.identity_payload()
        ):
            raise ValueError("audit_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "parameters": dict(sorted(self.parameters.items())),
            "query_id": self.query_id,
            "result_count": self.result_count,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"audit_id": self.audit_id, **self.identity_payload()}


def audit_wallet_relationship_intelligence_query(
    result: WalletRelationshipIntelligenceQueryResult,
    *,
    parameters: Mapping[str, str],
) -> WalletRelationshipIntelligenceQueryAuditReceipt:
    if not isinstance(result, WalletRelationshipIntelligenceQueryResult):
        raise TypeError("result must be WalletRelationshipIntelligenceQueryResult")
    if not isinstance(parameters, Mapping):
        raise TypeError("parameters must be a mapping")
    normalized = {str(key).strip(): str(value) for key, value in parameters.items()}
    if any(not key for key in normalized):
        raise ValueError("parameters must contain non-empty keys")
    identity = {
        "parameters": dict(sorted(normalized.items())),
        "query_id": result.query_id,
        "result_count": len(result.rows),
        "schema_version": _SCHEMA_VERSION,
    }
    return WalletRelationshipIntelligenceQueryAuditReceipt(
        **identity,
        audit_id=deterministic_id(
            "wallet_relationship_intelligence_query_audit", identity
        ),
    )


__all__ = [
    "WalletRelationshipIntelligenceQueryAuditReceipt",
    "audit_wallet_relationship_intelligence_query",
]
