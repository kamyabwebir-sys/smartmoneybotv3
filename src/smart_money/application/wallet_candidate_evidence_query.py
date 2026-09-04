from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_candidate_evidence import WalletCandidateEvidenceStatus
from smart_money.application.wallet_candidate_evidence_read_model import (
    WalletCandidateEvidenceReadModel,
    WalletCandidateEvidenceReadRow,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_candidate_evidence_query.v1"


@dataclass(frozen=True, slots=True)
class WalletCandidateEvidenceQueryResult:
    rows: tuple[WalletCandidateEvidenceReadRow, ...]
    query_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple) or not all(
            isinstance(item, WalletCandidateEvidenceReadRow) for item in self.rows
        ):
            raise TypeError("rows must be tuple of WalletCandidateEvidenceReadRow")
        if not isinstance(self.query_id, str) or not self.query_id.strip():
            raise ValueError("query_id must be non-empty")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet candidate evidence query schema_version")
        identity = {
            "evidence_ids": tuple(item.evidence.evidence_id for item in self.rows),
            "schema_version": self.schema_version,
        }
        if self.query_id != deterministic_id("wallet_candidate_evidence_query", identity):
            raise ValueError("query_id does not match result")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "rows": tuple(item.canonical_dict() for item in self.rows),
            "schema_version": self.schema_version,
        }


def query_wallet_candidate_evidence(
    model: WalletCandidateEvidenceReadModel,
    *,
    wallet: str | None = None,
    min_score_bps: int | None = None,
    max_rank: int | None = None,
    status: WalletCandidateEvidenceStatus | None = None,
    require_audit: bool = False,
) -> WalletCandidateEvidenceQueryResult:
    if not isinstance(model, WalletCandidateEvidenceReadModel):
        raise TypeError("model must be WalletCandidateEvidenceReadModel")
    if wallet is not None and (not isinstance(wallet, str) or not wallet.strip()):
        raise ValueError("wallet must be non-empty")
    for name, value in (("min_score_bps", min_score_bps), ("max_rank", max_rank)):
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise ValueError(f"{name} must be a non-negative integer")
    if status is not None and not isinstance(status, WalletCandidateEvidenceStatus):
        raise TypeError("status must be WalletCandidateEvidenceStatus")
    if not isinstance(require_audit, bool):
        raise TypeError("require_audit must be boolean")
    selected = tuple(
        row
        for row in model.rows
        if (wallet is None or row.evidence.feature.wallet == wallet.strip())
        and (
            min_score_bps is None
            or (row.ranking is not None and row.ranking.score_bps >= min_score_bps)
        )
        and (
            max_rank is None
            or (row.ranking is not None and row.ranking.rank <= max_rank)
        )
        and (status is None or row.evidence.status is status)
        and (not require_audit or row.audit is not None)
    )
    identity = {
        "evidence_ids": tuple(item.evidence.evidence_id for item in selected),
        "schema_version": _SCHEMA_VERSION,
    }
    return WalletCandidateEvidenceQueryResult(
        rows=selected,
        query_id=deterministic_id("wallet_candidate_evidence_query", identity),
    )


__all__ = ["WalletCandidateEvidenceQueryResult", "query_wallet_candidate_evidence"]
