# EM-003 Alignment — Separate Approval Request

Status: PENDING REVIEW
Decision: NOT RECORDED
Request Type: DOCUMENTATION/GOVERNANCE-ONLY
Requested Authority: LIMITED REPLACEMENT REVIEW
Implementation Authority Requested: NONE
Source Changes Requested: NO
Test Changes Requested: NO
Slice Unblock Requested: NO

---

## 1. Request Purpose

This document requests a separate and explicit governance review of the
EM-003 alignment defect in Slice 1.0.

This request does not approve or execute any repository replacement.

Creation or acceptance of this request does not grant implementation
authority.

---

## 2. Current Governance State

The authoritative state at the time of this request is:
```text
Slice Status: BLOCKED
Implementation Authority: NONE
Approval Status: NOT APPROVED
EM-003 Evidence Matrix Status: PARTIAL
EM-003 Verifier Expectation: MISSING
Replacement Authority: NONE

This request does not alter that state.

---

## 3. Repository-Grounded Mismatch

The current Slice 1.0 Evidence Matrix records EM-003 as:

text
PARTIAL

The Slice 1.0 governance verifier requires an EM-003 fragment containing:

text
MISSING | Need exact file and line references showing deterministic/replayable requirements.

These two governance artifacts therefore do not express the same EM-003
status.

The mismatch is classified as a governance consistency defect.

It is not classified as:

- a runtime defect;
- a domain-model defect;
- a serialization defect;
- an identifier defect;
- a registry defect;
- a source implementation defect;
- a test implementation defect.

---

## 4. Current Evidence-Matrix Reading

The current EM-003 row states that the repository already contains some
deterministic and replayable design constraints, while additional
specific references are required for full coverage.

The current status remains:

text
PARTIAL

This request does not claim that the current status is incorrect.

It requests review of whether the available repository-grounded evidence
supports a more precise governance status and matching verifier
assertion.

---

## 5. Requested Review Question

The Governance Owner and authorized reviewers are asked to decide:

text
Do the repository-grounded deterministic and replayable contract
references support classifying EM-003 as SUFFICIENT_FOR_REVIEW, while
explicitly avoiding any claim of implementation completeness?

Candidate answer requested for review:

text
EM-003 Evidence Status: SUFFICIENT_FOR_REVIEW

This is only a candidate status.

It must not be treated as effective unless a separate approval review
records an explicit and authorized:

text
Decision: APPROVED

---

## 6. Meaning of the Candidate Status

For this request, `SUFFICIENT_FOR_REVIEW` would mean only:

1. explicit deterministic constraints are documented in repository
   artifacts;
2. explicit replayability constraints are documented in repository
   artifacts;
3. the references are specific enough for governance review;
4. the Evidence Matrix and verifier may be aligned to one accepted
   governance reading.

It would not mean:

- implementation completeness;
- runtime correctness;
- full test coverage;
- approval of source behavior;
- approval of serialization behavior;
- approval of identifier algorithms;
- approval of validation behavior;
- approval of registry behavior;
- approval of execution or trading logic;
- Slice 1.0 completion;
- Slice 1.0 unblock;
- implementation authority.

---

## 7. Candidate Evidence Set

The separate approval review should inspect at least:

text
docs/core_contracts_principles.md
docs/deterministic_assumptions_v1.md
docs/evidence_policy_v1.md
docs/serialization_time_id_semantics_v1.md
docs/freeze_packs/slice_0_10.md
docs/freeze_packs/slice_1_0_evidence_matrix.md
docs/reviews/slice_1_0_governance_repair_review.md
src/smart_money/core/replay.py
tests/core/test_golden_replay.py
scripts/verify_slice_1_0_governance_repair.ps1

The current Evidence Matrix identifies candidate references including:

text
docs/core_contracts_principles.md:13
docs/deterministic_assumptions_v1.md:10-11
src/smart_money/core/replay.py:7
tests/core/test_golden_replay.py:3,12
docs/freeze_packs/slice_0_10.md:77,143

These references are review inputs, not automatically accepted findings.

The reviewer must verify the current repository contents and record exact
line references before approving any status change.

---

## 8. Requested Replacement Classification

If, and only if, the separate approval review is approved, the requested
replacement classification is:

text
Replacement Class: DOCUMENTATION/GOVERNANCE-ONLY
Runtime Behavior Change: NO
Source Change: NO
Test Change: NO
Public API Change: NO
Serialization Change: NO
Identifier Algorithm Change: NO
Validation Behavior Change: NO
Registry Behavior Change: NO
Package Boundary Change: NO
Module Move: NO
Broad Refactor: NO
Slice Unblock: NO
Implementation Authority Grant: NO

---

## 9. Maximum Candidate Replacement File Set

If the request is explicitly approved, the maximum candidate replacement
file set is:

text
docs/freeze_packs/slice_1_0_evidence_matrix.md
scripts/verify_slice_1_0_governance_repair.ps1

No other file is included in the requested replacement authority.

In particular, this request does not request changes under:

text
src/**
tests/**

---

## 10. Maximum Candidate Replacement Semantics

Subject to explicit approval, the requested replacement may only:

1. change the EM-003 Evidence Matrix status and note to the exact wording
   accepted by the separate approval review;
2. change the EM-003 verifier assertion to match that accepted Matrix
   wording;
3. preserve all unrelated Evidence Matrix rows;
4. preserve all unrelated verifier assertions;
5. preserve `Slice Status: BLOCKED`;
6. preserve `Implementation Authority: NONE`;
7. preserve the distinction between documented constraints and verified
   implementation completeness.

No implementation replacement is requested.

---

## 11. Requested Decision Outcomes

The separate approval review may record one of:

text
APPROVED
REJECTED
RETURNED_FOR_EVIDENCE_REPAIR

An approval, if issued, must use a decision type equivalent to:

text
Accepted as documentation-only replacement

Approval must be explicit, attributable, dated, and signed or recorded by
the authorized Governance Owner.

Silence, document creation, commit existence, reviewer discussion, or
partial checklist completion must not be interpreted as approval.

---

## 12. Approval Conditions

Approval is requested only if reviewers confirm all applicable items:

text
[ ] The Matrix/verifier mismatch was independently reproduced.
[ ] Exact deterministic evidence references were verified.
[ ] Exact replayability evidence references were verified.
[ ] Evidence-policy compatibility was verified.
[ ] The candidate status does not imply implementation completeness.
[ ] The replacement file set is exact and limited.
[ ] No source change is authorized.
[ ] No test change is authorized.
[ ] No runtime behavior change is authorized.
[ ] Slice 1.0 remains BLOCKED.
[ ] Implementation Authority remains NONE.
[ ] Required reviewer and Governance Owner sign-offs are complete.

If required evidence is absent, ambiguous, stale, or insufficient, this
request should be returned for evidence repair or rejected.

---

## 13. Required Separate Approval Artifact

This request requires a separate review artifact:

text
docs/reviews/em_003_alignment_separate_approval_review.md

That review should record:

- the authoritative input set;
- exact repository-grounded evidence references;
- mismatch reproduction;
- scope determination;
- decision outcome;
- decision owner;
- decision date;
- required sign-offs;
- final governance reading;
- post-decision handoff conditions.

This request is not a substitute for that review.

---

## 14. Non-Authorization Statement

Unless and until a valid separate approval review records an authorized
`Decision: APPROVED`, this request grants no permission to modify:

text
docs/freeze_packs/slice_1_0_evidence_matrix.md
scripts/verify_slice_1_0_governance_repair.ps1
src/**
tests/**

This request never grants authority for:

- execution or trading logic;
- risk calculation;
- opaque ML decisioning;
- reporting/UI leakage into core/domain logic;
- model or public API changes;
- serialization behavior changes;
- identifier algorithm changes;
- validation behavior changes;
- ingestion changes;
- registry changes;
- package rename;
- module move;
- broad refactor;
- Slice 1.0 unblock;
- implementation authority.

---

## 15. Requester Record

text
Requester Name:
Requester Role:
Request Date:
Repository Branch: docs/em-003-alignment-approval-request-final
Baseline Commit: 971a39bca66061db025e3be323c45ddd06c70eb6
Signature/Recorded Submission:

Requester confirmations:

text
[ ] I confirm this is a governance-only request.
[ ] I confirm no replacement has been executed by this request.
[ ] I confirm Slice 1.0 remains BLOCKED.
[ ] I confirm Implementation Authority remains NONE.
[ ] I confirm SUFFICIENT_FOR_REVIEW is only a candidate status.

Blank requester fields must not be interpreted as completed sign-off.

---

## 16. Current Request Conclusion

Current state:

text
Request Status: PENDING REVIEW
Decision: NOT RECORDED
Slice Status: BLOCKED
Implementation Authority: NONE
Replacement Authority: NONE
EM-003 Effective Status: PARTIAL
EM-003 Candidate Status: SUFFICIENT_FOR_REVIEW

No Matrix or verifier replacement is authorized by this request.

