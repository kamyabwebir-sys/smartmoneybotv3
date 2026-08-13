from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from contracts import EvidencePayload, ScoreReport

_DIRECTION_SCORES = {
    "bullish": Decimal("0.5"),
    "bearish": Decimal("-0.5"),
    "neutral": Decimal("0"),
}


class MarketScorer:
    """Produce a deterministic evidence score, never an execution decision."""

    def analyze(self, evidence_list: Iterable[EvidencePayload]) -> ScoreReport:
        evidence = tuple(evidence_list)
        if not evidence:
            return ScoreReport(
                score=Decimal("0"),
                reasoning="No evidence provided",
                evidence_count=0,
            )

        total_score = Decimal("0")
        structure_points = 0
        for item in evidence:
            if not isinstance(item, EvidencePayload):
                raise TypeError("all evidence items must be EvidencePayload")

            if item.evidence_type != "market_structure":
                continue

            structure_points += 1
            direction = item.data.get("direction", "neutral")
            if isinstance(direction, str):
                total_score += _DIRECTION_SCORES.get(
                    direction.strip().lower(),
                    Decimal("0"),
                )

        final_score = max(Decimal("-1"), min(total_score, Decimal("1")))
        return ScoreReport(
            score=final_score,
            reasoning=(
                f"Analyzed {structure_points} structure points "
                f"from {len(evidence)} evidence items"
            ),
            evidence_count=len(evidence),
        )
