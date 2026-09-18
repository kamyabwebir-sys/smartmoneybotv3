from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from smart_money.application.wallet_candidate_evidence_query import (
    WalletCandidateEvidenceQueryResult,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_candidate_query_audit.v1"


@dataclass(frozen=True, slots=True)
class WalletCandidateQueryAuditReceipt:
    query_id: str
    result_count: int
    parameters: Mapping[str, str]
    audit_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.query_id, str) or not self.query_id.strip():
            raise ValueError("query_id must be non-empty")
        if isinstance(self.result_count, bool) or not isinstance(self.result_count, int) or self.result_count < 0:
            raise ValueError("result_count must be a non-negative integer")
        if not isinstance(self.parameters, Mapping) or not self.parameters:
            raise ValueError("parameters must be a non-empty mapping")
        if not all(isinstance(k, str) and k.strip() and isinstance(v, str) and v.strip() for k, v in self.parameters.items()):
            raise ValueError("parameters must contain non-empty text")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported schema_version")
        expected = deterministic_id("wallet_candidate_query_audit", self._identity())
        if self.audit_id != expected:
            raise ValueError("audit_id does not match receipt")

    def _identity(self) -> dict[str, Any]:
        return {
            "parameters": dict(sorted(self.parameters.items())),
            "query_id": self.query_id.strip(),
            "result_count": self.result_count,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {**self._identity(), "audit_id": self.audit_id}


def audit_wallet_candidate_query(
    result: WalletCandidateEvidenceQueryResult,
    *,
    parameters: Mapping[str, str],
) -> WalletCandidateQueryAuditReceipt:
    if not isinstance(result, WalletCandidateEvidenceQueryResult):
        raise TypeError("result must be WalletCandidateEvidenceQueryResult")
    normalized = {
        str(key).strip(): str(value).strip() for key, value in parameters.items()
    }
    identity = {
        "parameters": dict(sorted(normalized.items())),
        "query_id": result.query_id.strip(),
        "result_count": len(result.rows),
        "schema_version": _SCHEMA_VERSION,
    }
    return WalletCandidateQueryAuditReceipt(
        query_id=result.query_id,
        result_count=len(result.rows),
        parameters=normalized,
        audit_id=deterministic_id("wallet_candidate_query_audit", identity),
    )


__all__ = ["WalletCandidateQueryAuditReceipt", "audit_wallet_candidate_query"]
