# EM-003 Alignment — Separate Approval Request

Status: PENDING REVIEW
Decision: NOT RECORDED
Request Type: GOVERNANCE-ONLY EVIDENCE ALIGNMENT
Slice: 1.0 Governance Repair

Implementation Authority Requested: NONE
Source Changes Requested: NO
Test Changes Requested: NO
Slice Unblock Requested: NO

---

## 1. Purpose

This document requests a separate governance review for the narrow
alignment of EM-003.

This request is not an approval.

This request does not authorize changes to:

- source code;
- tests;
- runtime behavior;
- package structure;
- domain contracts;
- discovery registry behavior.

The requested review is limited to whether EM-003 may be aligned between
the Evidence Matrix and the governance verifier.

---

## 2. Current State

The current governance state is:
```text
Slice Status: BLOCKED
Implementation Authority: NONE
Approval Status: NOT APPROVED
EM-003 Evidence Matrix Status: PARTIAL
EM-003 Verifier Expectation: MISSING

No separate approval review for EM-003 has been recorded.

No `Decision: APPROVED` exists for EM-003.

---

## 3. Alignment Defect

The Evidence Matrix and verifier currently encode different expected
states for EM-003.

Current Evidence Matrix state:

text
EM-003: PARTIAL

Current verifier expectation:

text
EM-003: MISSING

This creates a governance-tooling mismatch.

This is not a runtime implementation defect.

---

## 4. Claim Under Review

The EM-003 claim under review is:

text
Repository already has deterministic and replayable design constraints.

The review should determine only whether the repository contains enough
explicit evidence to mark this claim as sufficiently grounded for review.

This does not mean:

- implementation is complete;
- replay behavior is fully verified;
- Slice 1.0 is unblocked;
- implementation authority is granted;
- any source or test change is approved.

---

## 5. Repository-Grounded Evidence

The following repository documents are expected to support the limited
EM-003 claim:

text
docs/core_contracts_principles.md
docs/deterministic_assumptions_v1.md
docs/evidence_policy_v1.md
docs/serialization_time_id_semantics_v1.md

Expected evidence themes:

- deterministic contracts;
- replayable behavior;
- canonical serialization;
- stable evidence under deterministic replay;
- frozen inputs;
- avoidance of hidden wall-clock dependency in core semantics;
- deterministic identifiers and time semantics.

Exact line references must be confirmed during review.

---

## 6. Requested Governance Outcome

The requested reviewer decision is one of:

text
APPROVED
REJECTED
RETURNED_FOR_EVIDENCE_REPAIR

Only `APPROVED` may authorize the narrow replacement described below.

If the decision is not `APPROVED`, no replacement is permitted.

---

## 7. Requested Replacement If Approved

If separately approved, the requested replacement is limited to:

text
docs/freeze_packs/slice_1_0_evidence_matrix.md
scripts/verify_slice_1_0_governance_repair.ps1

The requested semantic outcome is:

text
EM-003 Evidence Status: SUFFICIENT_FOR_REVIEW
EM-003 Matrix/Verifier Alignment: RESOLVED
Slice Status: BLOCKED
Implementation Authority: NONE

The replacement must not modify unrelated rows or unrelated verifier
assertions.

---

## 8. Proposed EM-003 Matrix Semantics

If approved, the EM-003 row may be changed to communicate:

text
The repository contains explicit deterministic and replayable design
constraints sufficient for governance review.

The row must also communicate:

text
This evidence status does not approve implementation.
This evidence status does not unblock Slice 1.0.
This evidence status does not grant implementation authority.

---

## 9. Proposed Verifier Semantics

If approved, the verifier may be changed so that it no longer expects
EM-003 to be `MISSING`.

Instead, it should verify that:

text
EM-003 is marked SUFFICIENT_FOR_REVIEW.
The matrix contains exact repository evidence references.
The matrix states that this does not grant implementation authority.
The matrix states that Slice 1.0 remains BLOCKED.

All unrelated verifier assertions must remain unchanged.

---

## 10. Prohibited Changes

This request does not authorize:

- changes under `src/`;
- changes under `tests/`;
- registry implementation changes;
- core/domain model changes;
- serialization changes;
- identifier changes;
- validation behavior changes;
- replay implementation changes;
- package rename;
- module move;
- broad refactor;
- execution logic;
- trading logic;
- risk calculation;
- opaque ML decisioning;
- reporting/UI leakage into core/domain logic;
- Slice 1.0 unblock.

---

## 11. Audit Requirements If Approved

If a separate review records `Decision: APPROVED`, the replacement audit
must record:

text
Repository:
Branch:
Baseline commit:
Resulting commit:
Replacement type:
Reason:
Expected effect:

Required hash evidence:

text
Evidence Matrix before SHA-256:
Evidence Matrix after SHA-256:
Verifier before SHA-256:
Verifier after SHA-256:

Required changed-file evidence:

text
git status --short
git diff --name-only
git diff --check

Required verifier command:

powershell
pwsh -NoProfile -File ./scripts/verify_slice_1_0_governance_repair.ps1

Required verification record:

text
Verifier exit code:
Verifier output:
All assertions passed: YES / NO

Required confirmations:

text
No src/ changes: YES / NO
No tests/ changes: YES / NO
Only approved files changed: YES / NO
Unrelated matrix rows unchanged: YES / NO
Unrelated verifier assertions unchanged: YES / NO
Slice remains BLOCKED: YES / NO
Implementation Authority remains NONE: YES / NO

---

## 12. Approval Gate

No replacement may occur unless all conditions below are true:

text
[ ] Separate approval review exists.
[ ] Decision: APPROVED is explicitly recorded.
[ ] Approved file set is explicit.
[ ] Approved semantic replacement is explicit.
[ ] Slice Status remains BLOCKED.
[ ] Implementation Authority remains NONE.
[ ] Source changes remain prohibited.
[ ] Test changes remain prohibited.

---

## 13. Requester Confirmation

text
Requester:
Role:
Date:
Branch:
Baseline Commit:

Confirmations:

text
[ ] This is a governance-only request.
[ ] This request is not an approval.
[ ] No implementation authority is requested.
[ ] No source changes are requested.
[ ] No test changes are requested.
[ ] Slice 1.0 remains BLOCKED.
[ ] Replacement requires separate explicit approval.

---

## 14. Conclusion

This document requests a separate approval review for the narrow
alignment of EM-003.

Until an authorized reviewer records `Decision: APPROVED`, no Evidence
Matrix or verifier replacement is permitted.
