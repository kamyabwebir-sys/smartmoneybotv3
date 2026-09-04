from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping
from smart_money.application.token_lifecycle_query import TokenLifecycleQueryResult
from smart_money.core.ids import deterministic_id

@dataclass(frozen=True, slots=True)
class TokenLifecycleQueryAuditReceipt:
    query_id: str
    result_count: int
    parameters: Mapping[str, str]
    audit_id: str
    schema_version: str = "token_lifecycle_query_audit.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.query_id, str) or not self.query_id.strip():
            raise ValueError("query_id must be non-empty")
        if isinstance(self.result_count, bool) or not isinstance(self.result_count, int) or self.result_count < 0:
            raise ValueError("result_count must be non-negative")
        if not isinstance(self.parameters, Mapping) or not self.parameters:
            raise ValueError("parameters must be non-empty")
        if not all(isinstance(k, str) and k.strip() and isinstance(v, str) and v.strip() for k, v in self.parameters.items()):
            raise ValueError("parameters must contain text")
        expected = deterministic_id("token_lifecycle_query_audit", self._identity())
        if self.audit_id != expected:
            raise ValueError("audit_id mismatch")

    def _identity(self) -> dict[str, Any]:
        return {"query_id": self.query_id.strip(), "result_count": self.result_count,
                "parameters": dict(sorted(self.parameters.items())), "schema_version": self.schema_version}

    def canonical_dict(self) -> dict[str, Any]:
        return {**self._identity(), "audit_id": self.audit_id}

def audit_token_lifecycle_query(result: TokenLifecycleQueryResult, *, parameters: Mapping[str, str]) -> TokenLifecycleQueryAuditReceipt:
    if not isinstance(result, TokenLifecycleQueryResult):
        raise TypeError("result must be TokenLifecycleQueryResult")
    normalized = {str(k).strip(): str(v).strip() for k, v in parameters.items()}
    identity = {"query_id": result.query_id, "result_count": len(result.rows),
                "parameters": dict(sorted(normalized.items())), "schema_version": "token_lifecycle_query_audit.v1"}
    return TokenLifecycleQueryAuditReceipt(result.query_id, len(result.rows), normalized,
        deterministic_id("token_lifecycle_query_audit", identity))

__all__ = ["TokenLifecycleQueryAuditReceipt", "audit_token_lifecycle_query"]
