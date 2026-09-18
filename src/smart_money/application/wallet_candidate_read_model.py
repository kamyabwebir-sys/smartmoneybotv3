from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_candidate_evidence import WalletCandidateEvidence
from smart_money.application.wallet_ranking import WalletRanking, WalletRankingRow
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_candidate_read_model.v1"


@dataclass(frozen=True, slots=True)
class WalletCandidateReadRow:
    evidence: WalletCandidateEvidence
    ranking: WalletRankingRow | None

    def __post_init__(self) -> None:
        if not isinstance(self.evidence, WalletCandidateEvidence):
            raise TypeError("evidence must be WalletCandidateEvidence")
        if self.ranking is not None and not isinstance(self.ranking, WalletRankingRow):
            raise TypeError("ranking must be WalletRankingRow or None")
        if self.ranking is not None and self.ranking.evidence_id != self.evidence.evidence_id:
            raise ValueError("ranking evidence_id mismatch")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "evidence": self.evidence.canonical_dict(),
            "ranking": None if self.ranking is None else self.ranking.canonical_dict(),
        }


@dataclass(frozen=True, slots=True)
class WalletCandidateReadModel:
    rows: tuple[WalletCandidateReadRow, ...]
    model_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple) or not all(
            isinstance(item, WalletCandidateReadRow) for item in self.rows
        ):
            raise TypeError("rows must be tuple of WalletCandidateReadRow")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet candidate read model schema_version")
        identity = {"rows": tuple(item.canonical_dict() for item in self.rows), "schema_version": self.schema_version}
        if self.model_id != deterministic_id("wallet_candidate_read_model", identity):
            raise ValueError("model_id does not match rows")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "rows": tuple(item.canonical_dict() for item in self.rows),
            "schema_version": self.schema_version,
        }


def build_wallet_candidate_read_model(
    evidence: tuple[WalletCandidateEvidence, ...],
    ranking: WalletRanking | None = None,
) -> WalletCandidateReadModel:
    if not isinstance(evidence, tuple) or not all(
        isinstance(item, WalletCandidateEvidence) for item in evidence
    ):
        raise TypeError("evidence must be tuple of WalletCandidateEvidence")
    if ranking is not None and not isinstance(ranking, WalletRanking):
        raise TypeError("ranking must be WalletRanking or None")
    ranking_by_evidence = {} if ranking is None else {
        row.evidence_id: row for row in ranking.rows
    }
    rows = tuple(
        WalletCandidateReadRow(item, ranking_by_evidence.get(item.evidence_id))
        for item in sorted(evidence, key=lambda item: item.feature.wallet)
    )
    identity = {"rows": tuple(item.canonical_dict() for item in rows), "schema_version": _SCHEMA_VERSION}
    return WalletCandidateReadModel(
        rows=rows,
        model_id=deterministic_id("wallet_candidate_read_model", identity),
    )


__all__ = [
    "WalletCandidateReadModel",
    "WalletCandidateReadRow",
    "build_wallet_candidate_read_model",
]
