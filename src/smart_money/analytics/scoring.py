from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from smart_money.core.frozen import deep_freeze
from smart_money.ingestion.contracts import EvidencePayload

_DIRECTION_SCORES = {
    "bullish": Decimal("0.5"),
    "bearish": Decimal("-0.5"),
    "neutral": Decimal("0"),
}


@dataclass(frozen=True, slots=True)
class ScoreReport:
    """Deterministic analytical score; never a trading decision."""

    score: Decimal
    reasoning: str
    evidence_count: int
    score_breakdown: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.score, Decimal):
            raise TypeError("score must be Decimal")
        if not self.score.is_finite():
            raise ValueError("score must be finite")
        if not Decimal("-1") <= self.score <= Decimal("1"):
            raise ValueError("score must be between -1 and 1")
        if not isinstance(self.reasoning, str) or not self.reasoning.strip():
            raise ValueError("reasoning must be a non-empty string")
        if isinstance(self.evidence_count, bool) or not isinstance(
            self.evidence_count, int
        ):
            raise TypeError("evidence_count must be an integer")
        if self.evidence_count < 0:
            raise ValueError("evidence_count must be non-negative")
        if not isinstance(self.score_breakdown, Mapping):
            raise TypeError("score_breakdown must be a mapping")

        object.__setattr__(
            self,
            "score_breakdown",
            deep_freeze(self.score_breakdown, "score_breakdown"),
        )


class MarketScorer:
    """Produce deterministic evidence scores with explainable components."""

    def analyze(self, evidence_list: Iterable[EvidencePayload]) -> ScoreReport:
        evidence = tuple(evidence_list)
        if not evidence:
            return ScoreReport(
                score=Decimal("0"),
                reasoning="No evidence provided",
                evidence_count=0,
                score_breakdown=self._build_breakdown(
                    evidence_count=0,
                    structure_count=0,
                    bullish_count=0,
                    bearish_count=0,
                    neutral_count=0,
                    unknown_direction_count=0,
                    raw_score=Decimal("0"),
                    bounded_score=Decimal("0"),
                ),
            )

        total_score = Decimal("0")
        structure_count = 0
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0
        unknown_direction_count = 0

        for item in evidence:
            if not isinstance(item, EvidencePayload):
                raise TypeError("all evidence items must be EvidencePayload")

            if item.evidence_type != "market_structure":
                continue

            structure_count += 1
            direction = item.data.get("direction", "neutral")
            normalized_direction = (
                direction.strip().lower() if isinstance(direction, str) else ""
            )
            if normalized_direction == "bullish":
                bullish_count += 1
            elif normalized_direction == "bearish":
                bearish_count += 1
            elif normalized_direction == "neutral":
                neutral_count += 1
            else:
                unknown_direction_count += 1

            total_score += _DIRECTION_SCORES.get(
                normalized_direction,
                Decimal("0"),
            )

        final_score = max(Decimal("-1"), min(total_score, Decimal("1")))
        return ScoreReport(
            score=final_score,
            reasoning=(
                f"Analyzed {structure_count} structure points "
                f"from {len(evidence)} evidence items"
            ),
            evidence_count=len(evidence),
            score_breakdown=self._build_breakdown(
                evidence_count=len(evidence),
                structure_count=structure_count,
                bullish_count=bullish_count,
                bearish_count=bearish_count,
                neutral_count=neutral_count,
                unknown_direction_count=unknown_direction_count,
                raw_score=total_score,
                bounded_score=final_score,
            ),
        )

    @staticmethod
    def _build_breakdown(
        *,
        evidence_count: int,
        structure_count: int,
        bullish_count: int,
        bearish_count: int,
        neutral_count: int,
        unknown_direction_count: int,
        raw_score: Decimal,
        bounded_score: Decimal,
    ) -> dict[str, Any]:
        return {
            "bearish_count": bearish_count,
            "bounded_score": bounded_score,
            "bullish_count": bullish_count,
            "evidence_count": evidence_count,
            "ignored_evidence_count": evidence_count - structure_count,
            "neutral_count": neutral_count,
            "raw_score": raw_score,
            "structure_count": structure_count,
            "unknown_direction_count": unknown_direction_count,
        }


__all__ = ["MarketScorer", "ScoreReport"]
