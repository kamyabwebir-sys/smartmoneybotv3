from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping
from smart_money.application.token_safety_candidate_query import TokenSafetyCandidateQueryResult
from smart_money.core.ids import deterministic_id

@dataclass(frozen=True, slots=True)
class TokenSafetyCandidateQueryAuditReceipt:
    query_id: str
    result_count: int
    parameters: Mapping[str, str]
    audit_id: str
    schema_version: str = "token_safety_candidate_query_audit.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.query_id, str) or not self.query_id.strip():
            raise ValueError("query_id must be non-empty")
        if isinstance(self.result_count, bool) or not isinstance(self.result_count, int) or self.result_count < 0:
            raise ValueError("result_count must be non-negative")
        if not isinstance(self.parameters, Mapping) or not self.parameters:
            raise ValueError("parameters must be non-empty")
        if self.audit_id != deterministic_id("token_safety_candidate_query_audit", self._identity()):
            raise ValueError("audit_id mismatch")

    def _identity(self) -> dict[str, Any]:
        return {"query_id": self.query_id.strip(), "result_count": self.result_count,
                "parameters": dict(sorted(self.parameters.items())), "schema_version": self.schema_version}

    def canonical_dict(self) -> dict[str, Any]:
        return {**self._identity(), "audit_id": self.audit_id}

def audit_token_safety_candidate_query(result: TokenSafetyCandidateQueryResult, *, parameters: Mapping[str, str]) -> TokenSafetyCandidateQueryAuditReceipt:
    if not isinstance(result, TokenSafetyCandidateQueryResult):
        raise TypeError("result must be TokenSafetyCandidateQueryResult")
    normalized = {str(k).strip(): str(v).strip() for k, v in parameters.items()}
    identity = {"query_id": result.query_id, "result_count": len(result.rows),
                "parameters": dict(sorted(normalized.items())), "schema_version": "token_safety_candidate_query_audit.v1"}
    return TokenSafetyCandidateQueryAuditReceipt(result.query_id, len(result.rows), normalized,
        deterministic_id("token_safety_candidate_query_audit", identity))

__all__ = ["TokenSafetyCandidateQueryAuditReceipt", "audit_token_safety_candidate_query"]
