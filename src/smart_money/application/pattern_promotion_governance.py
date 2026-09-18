from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from smart_money.application.pattern_governance import PatternRegistryProposal
from smart_money.core.ids import deterministic_id


class PatternReviewDecision(str):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"


@dataclass(frozen=True, slots=True)
class PatternProposalStore:
    path: Path
    _items: dict[str, PatternRegistryProposal] | None = None

    def save(self, proposal: PatternRegistryProposal) -> str:
        if not isinstance(proposal, PatternRegistryProposal):
            raise TypeError("proposal must be PatternRegistryProposal")
        items = dict(self._items or {})
        items[proposal.proposal_id] = proposal
        object.__setattr__(self, "_items", items)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(
            {"schema_version": "pattern_proposal_store.v1",
             "items": [item.canonical_dict() if hasattr(item, "canonical_dict") else {
                 "observation_id": item.observation_id, "rationale": item.rationale,
                 "proposal_id": item.proposal_id, "schema_version": item.schema_version,
             } for item in items.values()]},
            sort_keys=True, separators=(",", ":")), encoding="utf-8")
        return proposal.proposal_id


@dataclass(frozen=True, slots=True)
class PatternReview:
    proposal_id: str
    decision: str
    reviewer: str
    rationale: str
    review_id: str
    schema_version: str = "pattern_review.v1"

    def __post_init__(self) -> None:
        if self.decision not in {PatternReviewDecision.APPROVED, PatternReviewDecision.REJECTED, PatternReviewDecision.PENDING}:
            raise ValueError("unsupported review decision")
        for name in ("proposal_id", "reviewer", "rationale"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        expected = deterministic_id("pattern_review", self.identity_payload())
        if self.review_id != expected:
            raise ValueError("review_id mismatch")

    def identity_payload(self) -> dict[str, Any]:
        return {"decision": self.decision, "proposal_id": self.proposal_id.strip(),
                "rationale": self.rationale.strip(), "reviewer": self.reviewer.strip(),
                "schema_version": self.schema_version}


@dataclass(frozen=True, slots=True)
class PatternValidationWindow:
    proposal_id: str
    start_slot: int
    end_slot: int
    sample_count: int
    success_count: int
    window_id: str
    schema_version: str = "pattern_validation_window.v1"

    def __post_init__(self) -> None:
        if self.end_slot < self.start_slot or self.sample_count < 0 or not 0 <= self.success_count <= self.sample_count:
            raise ValueError("invalid validation window")
        identity = self.identity_payload()
        if self.window_id != deterministic_id("pattern_validation_window", identity):
            raise ValueError("window_id mismatch")

    def identity_payload(self) -> dict[str, Any]:
        return {"end_slot": self.end_slot, "proposal_id": self.proposal_id.strip(),
                "sample_count": self.sample_count, "schema_version": self.schema_version,
                "start_slot": self.start_slot, "success_count": self.success_count}


@dataclass(frozen=True, slots=True)
class PatternPromotionGate:
    proposal_id: str
    review_id: str
    window_id: str
    promoted: bool
    gate_id: str
    schema_version: str = "pattern_promotion_gate.v1"

    def __post_init__(self) -> None:
        expected = deterministic_id("pattern_promotion_gate", {
            "proposal_id": self.proposal_id, "review_id": self.review_id,
            "window_id": self.window_id, "promoted": self.promoted,
            "schema_version": self.schema_version})
        if self.gate_id != expected:
            raise ValueError("gate_id mismatch")


def evaluate_promotion_gate(proposal: PatternRegistryProposal, review: PatternReview,
                            window: PatternValidationWindow) -> PatternPromotionGate:
    if review.proposal_id != proposal.proposal_id or window.proposal_id != proposal.proposal_id:
        raise ValueError("proposal identity mismatch")
    promoted = review.decision == PatternReviewDecision.APPROVED and window.sample_count > 0 and window.success_count > 0
    identity = {"proposal_id": proposal.proposal_id, "review_id": review.review_id,
                "window_id": window.window_id, "promoted": promoted,
                "schema_version": "pattern_promotion_gate.v1"}
    return PatternPromotionGate(proposal.proposal_id, review.review_id, window.window_id,
                                promoted, deterministic_id("pattern_promotion_gate", identity))


__all__ = ["PatternProposalStore", "PatternReviewDecision", "PatternReview",
           "PatternValidationWindow", "PatternPromotionGate", "evaluate_promotion_gate"]
