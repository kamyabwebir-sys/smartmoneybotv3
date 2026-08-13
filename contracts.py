from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from smart_money.ingestion.contracts import EvidencePayload, IngestionResult


@dataclass(frozen=True, slots=True)
class GroundedEntry:
    canonical_id: str
    payload: EvidencePayload

    def __post_init__(self) -> None:
        if not isinstance(self.canonical_id, str) or not self.canonical_id.strip():
            raise ValueError("canonical_id must be a non-empty string")
        if not isinstance(self.payload, EvidencePayload):
            raise TypeError("payload must be an EvidencePayload")
        if self.canonical_id != self.payload.get_canonical_id():
            raise ValueError("canonical_id does not match payload content")


@dataclass(frozen=True, slots=True)
class ScoreReport:
    """Deterministic analytical score; never a trading decision."""

    score: Decimal
    reasoning: str
    evidence_count: int

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


__all__ = [
    "EvidencePayload",
    "GroundedEntry",
    "IngestionResult",
    "ScoreReport",
]
