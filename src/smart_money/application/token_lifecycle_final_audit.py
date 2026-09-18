from __future__ import annotations
from dataclasses import dataclass
from smart_money.application.token_outcome_query import TokenOutcomeQueryResult
from smart_money.core.ids import deterministic_id

@dataclass(frozen=True, slots=True)
class TokenLifecycleFinalAuditReceipt:
    query_id: str
    outcome_count: int
    audit_id: str
    schema_version: str = "token_lifecycle_final_audit.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.query_id, str) or not self.query_id.strip():
            raise ValueError("query_id must be non-empty")
        if isinstance(self.outcome_count, bool) or not isinstance(self.outcome_count, int) or self.outcome_count < 0:
            raise ValueError("outcome_count must be non-negative")
        expected = deterministic_id("token_lifecycle_final_audit", {
            "outcome_count": self.outcome_count, "query_id": self.query_id.strip(),
            "schema_version": self.schema_version})
        if self.audit_id != expected:
            raise ValueError("audit_id mismatch")

    def canonical_dict(self) -> dict[str, object]:
        return {"audit_id": self.audit_id, "outcome_count": self.outcome_count,
                "query_id": self.query_id.strip(), "schema_version": self.schema_version}

def build_token_lifecycle_final_audit(result: TokenOutcomeQueryResult) -> TokenLifecycleFinalAuditReceipt:
    if not isinstance(result, TokenOutcomeQueryResult):
        raise TypeError("result must be TokenOutcomeQueryResult")
    identity = {"outcome_count": len(result.rows), "query_id": result.query_id,
                "schema_version": "token_lifecycle_final_audit.v1"}
    return TokenLifecycleFinalAuditReceipt(result.query_id, len(result.rows),
        deterministic_id("token_lifecycle_final_audit", identity))

__all__ = ["TokenLifecycleFinalAuditReceipt", "build_token_lifecycle_final_audit"]
