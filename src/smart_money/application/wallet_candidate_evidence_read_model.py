from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_candidate_evidence import WalletCandidateEvidence
from smart_money.application.wallet_candidate_evidence_audit import (
    WalletCandidateEvidenceAuditReceipt,
)
from smart_money.application.wallet_ranking import WalletRankingRow
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_candidate_evidence_read_model.v1"


@dataclass(frozen=True, slots=True)
class WalletCandidateEvidenceReadRow:
    evidence: WalletCandidateEvidence
    ranking: WalletRankingRow | None
    audit: WalletCandidateEvidenceAuditReceipt | None

    def __post_init__(self) -> None:
        if not isinstance(self.evidence, WalletCandidateEvidence):
            raise TypeError("evidence must be WalletCandidateEvidence")
        if self.ranking is not None and not isinstance(self.ranking, WalletRankingRow):
            raise TypeError("ranking must be WalletRankingRow or None")
        if self.audit is not None and not isinstance(
            self.audit, WalletCandidateEvidenceAuditReceipt
        ):
            raise TypeError("audit must be WalletCandidateEvidenceAuditReceipt or None")
        if self.ranking is not None and self.ranking.evidence_id != self.evidence.evidence_id:
            raise ValueError("ranking evidence_id mismatch")
        if self.audit is not None and self.audit.evidence_id != self.evidence.evidence_id:
            raise ValueError("audit evidence_id mismatch")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "audit": None if self.audit is None else self.audit.canonical_dict(),
            "evidence": self.evidence.canonical_dict(),
            "ranking": None if self.ranking is None else self.ranking.canonical_dict(),
        }


@dataclass(frozen=True, slots=True)
class WalletCandidateEvidenceReadModel:
    rows: tuple[WalletCandidateEvidenceReadRow, ...]
    model_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple) or not all(
            isinstance(item, WalletCandidateEvidenceReadRow) for item in self.rows
        ):
            raise TypeError("rows must be tuple of WalletCandidateEvidenceReadRow")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet candidate evidence read model schema_version")
        identity = {
            "rows": tuple(item.canonical_dict() for item in self.rows),
            "schema_version": self.schema_version,
        }
        if self.model_id != deterministic_id("wallet_candidate_evidence_read_model", identity):
            raise ValueError("model_id does not match rows")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "rows": tuple(item.canonical_dict() for item in self.rows),
            "schema_version": self.schema_version,
        }


def build_wallet_candidate_evidence_read_model(
    evidence: tuple[WalletCandidateEvidence, ...],
    *,
    ranking_rows: tuple[WalletRankingRow, ...] = (),
    audits: tuple[WalletCandidateEvidenceAuditReceipt, ...] = (),
) -> WalletCandidateEvidenceReadModel:
    if not isinstance(evidence, tuple) or not all(
        isinstance(item, WalletCandidateEvidence) for item in evidence
    ):
        raise TypeError("evidence must be tuple of WalletCandidateEvidence")
    if not isinstance(ranking_rows, tuple) or not all(
        isinstance(item, WalletRankingRow) for item in ranking_rows
    ):
        raise TypeError("ranking_rows must be tuple of WalletRankingRow")
    if not isinstance(audits, tuple) or not all(
        isinstance(item, WalletCandidateEvidenceAuditReceipt) for item in audits
    ):
        raise TypeError("audits must be tuple of WalletCandidateEvidenceAuditReceipt")
    ranking_by_id = {item.evidence_id: item for item in ranking_rows}
    audit_by_id = {item.evidence_id: item for item in audits}
    rows = tuple(
        WalletCandidateEvidenceReadRow(
            item,
            ranking_by_id.get(item.evidence_id),
            audit_by_id.get(item.evidence_id),
        )
        for item in sorted(evidence, key=lambda item: item.feature.wallet)
    )
    identity = {"rows": tuple(item.canonical_dict() for item in rows), "schema_version": _SCHEMA_VERSION}
    return WalletCandidateEvidenceReadModel(
        rows=rows,
        model_id=deterministic_id("wallet_candidate_evidence_read_model", identity),
    )


__all__ = [
    "WalletCandidateEvidenceReadModel",
    "WalletCandidateEvidenceReadRow",
    "build_wallet_candidate_evidence_read_model",
]
