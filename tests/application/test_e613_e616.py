from pathlib import Path

from smart_money.application.pattern_discovery import extract_wallet_behavior_pattern
from smart_money.application.pattern_governance import propose_pattern
from smart_money.application.pattern_promotion_governance import (
    PatternProposalStore, PatternReview, PatternReviewDecision, PatternValidationWindow,
    evaluate_promotion_gate,
)
from smart_money.core.ids import deterministic_id


def test_pattern_promotion_governance(tmp_path: Path) -> None:
    pattern = extract_wallet_behavior_pattern("wallet", features=("early_entry",), source_id="test")
    proposal = propose_pattern(pattern, "validated hypothesis")
    store = PatternProposalStore(tmp_path / "proposals.json")
    assert store.save(proposal) == proposal.proposal_id
    review_identity = {"decision": "APPROVED", "proposal_id": proposal.proposal_id,
                       "rationale": "reviewed", "reviewer": "human",
                       "schema_version": "pattern_review.v1"}
    review = PatternReview(proposal.proposal_id, PatternReviewDecision.APPROVED, "human", "reviewed",
                           deterministic_id("pattern_review", review_identity))
    window_identity = {"end_slot": 20, "proposal_id": proposal.proposal_id, "sample_count": 2,
                       "schema_version": "pattern_validation_window.v1", "start_slot": 10,
                       "success_count": 1}
    window = PatternValidationWindow(proposal.proposal_id, 10, 20, 2, 1,
                                     deterministic_id("pattern_validation_window", window_identity))
    assert evaluate_promotion_gate(proposal, review, window).promoted
