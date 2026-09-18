from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_candidate_evidence import WalletCandidateEvidence
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_ranking.v1"


@dataclass(frozen=True, slots=True)
class WalletRankingRow:
    evidence_id: str
    wallet: str
    rank: int
    score_bps: int

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "rank": self.rank,
            "score_bps": self.score_bps,
            "wallet": self.wallet,
        }


@dataclass(frozen=True, slots=True)
class WalletRanking:
    rows: tuple[WalletRankingRow, ...]
    ranking_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple) or not all(
            isinstance(item, WalletRankingRow) for item in self.rows
        ):
            raise TypeError("rows must be tuple of WalletRankingRow")
        if tuple(item.rank for item in self.rows) != tuple(range(1, len(self.rows) + 1)):
            raise ValueError("ranks must be contiguous and one-based")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet ranking schema_version")
        identity = {
            "rows": tuple(item.canonical_dict() for item in self.rows),
            "schema_version": self.schema_version,
        }
        if self.ranking_id != deterministic_id("wallet_ranking", identity):
            raise ValueError("ranking_id does not match rows")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "ranking_id": self.ranking_id,
            "rows": tuple(item.canonical_dict() for item in self.rows),
            "schema_version": self.schema_version,
        }


def rank_wallet_candidates(
    evidence: tuple[WalletCandidateEvidence, ...],
) -> WalletRanking:
    if not isinstance(evidence, tuple) or not all(
        isinstance(item, WalletCandidateEvidence) for item in evidence
    ):
        raise TypeError("evidence must be tuple of WalletCandidateEvidence")

    def score(item: WalletCandidateEvidence) -> int:
        feature = item.feature
        return (
            feature.early_entry_consistency_bps * 4
            + feature.buy_ratio_bps * 2
            + feature.data_completeness_bps * 2
            + min(feature.relationship_count, 100) * 100
            + min(feature.cohort_count, 100) * 50
        ) // 10

    ordered = sorted(
        evidence,
        key=lambda item: (-score(item), item.feature.wallet, item.evidence_id),
    )
    rows = tuple(
        WalletRankingRow(
            evidence_id=item.evidence_id,
            wallet=item.feature.wallet,
            rank=index,
            score_bps=score(item),
        )
        for index, item in enumerate(ordered, start=1)
    )
    identity = {
        "rows": tuple(item.canonical_dict() for item in rows),
        "schema_version": _SCHEMA_VERSION,
    }
    return WalletRanking(
        rows=rows,
        ranking_id=deterministic_id("wallet_ranking", identity),
    )


__all__ = ["WalletRanking", "WalletRankingRow", "rank_wallet_candidates"]
