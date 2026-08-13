# Slice 1.48 Non-Authoritative Batch Governance Proposal

## Status
- Slice: 1.48
- Authority Status: NON-AUTHORITATIVE
- Implementation Authority: NONE
- Scope: documentation_only
- Enforcement: none

## Intent
Produce a compact non-authoritative governance proposal pack for related follow-up coordination without granting implementation authority or changing any protected runtime contract.

## In Scope
- governance documentation
- governance review documentation
- deterministic receipt capture
- evidence-first coordination notes

## Out of Scope
- execution or trading logic
- risk calculation
- opaque ML decisioning
- verifier or promotion gate changes
- registry changes
- protected file changes

## Protected Files
- src/smart_money/discovery/registry.py
- tests/discovery/test_registry.py

## Deliverables
- docs/governance/proposals/slice_1_48_non_authoritative_batch_governance_proposal.md
- docs/governance/reviews/slice_1_48_non_authoritative_batch_governance_proposal_review.md
- artifacts/governance/slice_1_48_non_authoritative_batch_governance_proposal.receipt.json

## Acceptance Conditions
- deterministic output only
- replayable output only
- no timestamps in receipt
- no absolute paths in receipt
- no machine-specific values in receipt
- no implementation authority granted
- no protected files modified

## Non-Approval Boundary
This artifact is documentation-only and non-authoritative. It does not approve implementation, promotion, enforcement, or registry modification.