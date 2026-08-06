# Post Slice 1.31 Next Scope Grounding Proposal

Status: PROPOSAL_ONLY
Authority: NON_AUTHORITATIVE
Implementation/Promotion Authority: NO
Promotion Gate: LOCKED
Mode: INVENTORY_ONLY / READ_ONLY
Lane: FAST_LANE_CANDIDATE_ONLY
Slice Creation: NO_NUMBERED_SLICE_CREATED
Installer: NOT_INCLUDED
Verifier: NOT_INCLUDED
Receipt: NOT_INCLUDED

---

## 1. Purpose

This document proposes a non-authoritative grounding envelope for selecting the next safe governance scope after Slice 1.31.

It is intended only to clarify the governance authority chain, backlog priority interpretation, and safe candidate work lanes.

This document does not authorize implementation, promotion, code mutation, execution behavior, trading logic, risk calculation, ML decisioning, reporting/UI behavior, or changes to protected files.

This document does not create Slice 1.32 or any other numbered slice.

---

## 2. Frozen Governance Context

The current governance baseline remains locked after Slice 1.31.

The following constraints are treated as controlling context:

- EM-003 Status: CONTRACT_LOCKED
- Promotion Gate: LOCKED
- Implementation/Promotion Authority: NO
- Inventory Mode remains active
- Read-Only posture remains active
- All post-1.31 executable artifacts remain Not Grounded unless separately authorized by an explicit grounded governance artifact

The Slice 1.31 closure review states that the promotion gate is locked and implementation/promotion authority is not granted.

Therefore, any post-1.31 work must remain proposal-only unless a future grounded authority chain explicitly unlocks implementation.

---

## 3. Authority Chain Clarification

This proposal interprets the Slice 1.31 governance backlog approval as backlog prioritization readiness only.

The phrase:

> Ready for implementation. No leakage into core/domain logic detected.

must not be interpreted as an implementation authority grant.

For this proposal, the safe interpretation is:

- backlog candidates may be classified and discussed;
- priority order may be reasoned about;
- governance-only scope may be proposed;
- no implementation may begin;
- no promotion may occur;
- no installer, verifier, receipt, or executable artifact may be introduced by this document.

If there is any conflict between backlog readiness language and explicit authority language, the explicit authority language wins:

> Implementation/Promotion Authority: NO
> Promotion Gate: LOCKED

This document therefore remains fail-closed with respect to implementation.

---

## 4. Operating Rule Envelope

The applicable operating rules for future governance work are:

- maximum 3 primary files per governance slice;
- maximum 1 installer;
- maximum 1 verifier;
- maximum 1 evidence/review artifact;
- Fast Lane is limited to Patch / Verifier / Evidence / Canonicalization;
- Deep Lane includes Architecture / Domain Contracts / Refactor and requires explicit intent;
- fail-closed conditions include:
  - CANONICAL_HASH_DRIFT
  - PROTECTED_FILE_MUTATION
  - EVIDENCE_GROUNDING_GAP
- no execution logic;
- no trading logic;
- no risk calculation;
- no ML decisioning in Core/Domain.

This proposal does not consume the slice budget because it does not create a numbered implementation slice.

---

## 5. Protected Files

The following files remain protected and must not be modified by this proposal:

- `src/smart_money/discovery/registry.py`
- `tests/discovery/test_registry.py`

Any future proposal that requires changes to these files must explicitly declare that intent and must be reviewed as a separate grounded governance action.

This proposal requires no protected file mutation.

---

## 6. Backlog Priority Formula

Future candidate work may be ranked using the approved priority formula:
```text
PriorityScore = (4 * UnlockValue) + (3 * DeterminismRisk) + (2 * ScopeSafety) + (1 * LowCost)

The formula is advisory for prioritization only.

It does not grant authority to implement any candidate item.

Each score component should be interpreted as follows:

| Component | Meaning |
|---|---|
| UnlockValue | How much the candidate unblocks safe future governance progress |
| DeterminismRisk | How directly the candidate reduces deterministic/replayability uncertainty |
| ScopeSafety | How unlikely the candidate is to leak into Core/Domain/Execution scope |
| LowCost | How small and low-friction the candidate is to review and ground |

Higher scores indicate better candidates for future proposal or review sequencing.

---

## 7. Candidate Backlog Lanes

The accepted backlog categories are:

### P0 — Governance Stabilization

Candidate themes:

- canonical drift clarification;
- fail-closed wording repairs;
- authority chain disambiguation;
- missing or ambiguous governance evidence classification;
- explicit prevention of implementation authority leakage.

P0 items are preferred when they reduce ambiguity without touching runtime code.

### P1 — Near-Term Hardening

Candidate themes:

- verifier gate contracts;
- artifact shape contracts;
- evidence output constraints;
- receipt schema clarification;
- grounded review checklist improvements.

P1 items may become implementation candidates only after explicit authority is granted.

### P2 — Process Standardization

Candidate themes:

- repair registry governance;
- slice budget enforcement;
- naming conventions;
- proposal/review template normalization;
- deterministic governance workflow documentation.

P2 items should remain procedural unless explicitly scoped otherwise.

---

## 8. Recommended Next Safe Scope

The recommended next safe scope is:

text
Governance Authority Chain Clarification

Recommended classification:

text
PROPOSAL_ONLY
NON_AUTHORITATIVE
FAST_LANE
READ_ONLY
NO_IMPLEMENTATION_AUTHORITY

Recommended objective:

text
Clarify how post-1.31 candidate work can be proposed, scored, reviewed, and rejected without granting implementation or promotion authority.

Recommended candidate output:

text
One non-authoritative proposal or review artifact only.

Not recommended at this stage:

- new installer;
- new verifier;
- new receipt;
- numbered Slice 1.32;
- protected file mutation;
- Core/Domain refactor;
- registry repair;
- evidence generation;
- promotion gate change.

---

## 9. Acceptance Envelope

A future review may approve this proposal only if all of the following remain true:

- scope remains governance-only;
- determinism is preserved;
- replayability is preserved;
- protected files remain unchanged;
- no forbidden trading/risk/ML tokens are introduced;
- no implementation authority is granted;
- no promotion authority is granted;
- no executable artifact is introduced;
- no numbered slice is created;
- no Core/Domain behavior changes;
- no reporting/UI leakage into Core/Domain;
- no opaque ML decisioning is introduced.

If any condition is violated, the safe verdict is `patch_required` or `fail_closed`.

---

## 10. Review Verdict Options

Allowed review verdicts for this proposal are limited to:

text
approve_as_non_authoritative_proposal
patch_required
fail_closed

The preferred successful verdict is:

text
approve_as_non_authoritative_proposal

This means:

- the proposal is acceptable as a non-authoritative governance clarification;
- it does not authorize implementation;
- it does not unlock promotion;
- it does not create a new slice;
- it does not mutate protected files.

The verdict `approve` should be avoided because it may be misread as an implementation approval.

The verdict `ready_for_implementation` should be avoided unless a separate grounded authority artifact explicitly grants implementation authority.

---

## 11. Explicit Non-Goals

This proposal does not:

- implement code;
- modify source files;
- modify tests;
- modify protected registry files;
- create Slice 1.32;
- create or run an installer;
- create or run a verifier;
- create or capture a receipt;
- generate evidence;
- adjudicate evidence;
- unlock EM-003 promotion;
- alter the promotion gate;
- grant implementation authority;
- grant verifier authority;
- introduce trading logic;
- introduce execution logic;
- introduce risk calculation;
- introduce ML decisioning;
- introduce reporting/UI behavior;
- refactor architecture;
- change domain contracts.

---

## 12. Fail-Closed Rules

This proposal must be treated as fail-closed if any future patch or interpretation attempts to use it to justify:

- implementation;
- promotion;
- executable artifact creation;
- verifier creation;
- installer creation;
- receipt creation;
- protected file mutation;
- Core/Domain logic change;
- trading, execution, risk, or ML decision behavior;
- ungrounded post-1.31 slice promotion.

If ambiguity exists, the safe interpretation is:

text
NO AUTHORITY GRANTED

---

## 13. Minimal Future Work Path

The safest future path is:

1. Approve this document only as a non-authoritative proposal.
2. Keep Inventory Mode active.
3. Keep Read-Only posture active.
4. Do not create a numbered slice.
5. Use the priority formula only to rank candidate governance work.
6. Require a separate grounded authority artifact before any implementation.
7. Preserve protected files unchanged.
8. Prefer Fast Lane governance clarification over Deep Lane architecture/refactor work.

---

## 14. Source Grounding

This proposal is grounded in the following governance artifacts:

- `docs/freeze_packs/slice_1_31_governance_operating_rules_freeze_pack.md`
  - Slice budget: lines 6-7
  - Fast Lane / Deep Lane: lines 10-11
  - Failure taxonomy: line 14
  - Guardrails against execution/risk/ML leakage: line 17

- `docs/governance/reviews/slice_1_31_em_003_governance_receipt_contract_lock_closure_review.md`
  - Review Verdict: line 3
  - EM-003 Status: line 5
  - Promotion Gate: line 7
  - Implementation/Promotion Authority: line 9
  - No execution/trading/risk/ML/reporting/registry mutation: line 17

- `docs/reviews/slice_1_31_governance_backlog_prioritization_review.md`
  - Status: line 2
  - Priority formula: line 6
  - P0/P1/P2 backlog categories: lines 9-11
  - Backlog readiness wording: line 14

- `docs/reviews/slice_1_26_governance_backlog_review.md`
  - Status Draft: line 3
  - Verdict options including patch-required and fail-closed: lines 7-8
  - Acceptance constraints: lines 11-15
  - Patch-required condition: line 20

---

## 15. Final Governance Position

This document is safe only as a non-authoritative governance proposal.

Final position:

text
APPROVE ONLY AS NON-AUTHORITATIVE PROPOSAL
NO IMPLEMENTATION AUTHORITY
NO PROMOTION AUTHORITY
NO NUMBERED SLICE
NO EXECUTABLE ARTIFACTS
NO PROTECTED FILE MUTATION
FAIL-CLOSED ON AMBIGUITY