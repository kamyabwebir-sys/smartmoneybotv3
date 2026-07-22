# EM-003 Alignment Separate Approval Request

Review Type: Separate Approval Request  
Scope: Governance-only / Docs-only  
Requested Authority: Limited artifact-alignment authority  
Current Implementation Authority: NONE  
Current Slice Status: BLOCKED  
Current Approval Status: NOT APPROVED  
Current EM-003 Status: PARTIAL  

---

## 1. Purpose

This document requests a separate explicit approval to decide the authorized alignment path for EM-003 evidence verification.

This request exists because EM-003 has a documented historical/archive verifier and Evidence Matrix wording mismatch, while later live-branch inspection indicates that the active verifier appears aligned with the current EM-003 PARTIAL note.

This document does not itself approve implementation work, source changes, test changes, verifier mutation, Evidence Matrix mutation, or Slice unblocking.

---

## 2. Current Governance State

The current governance state remains:

- Slice Status: BLOCKED
- Implementation Authority: NONE
- Approval Status: NOT APPROVED
- EM-003 Status: PARTIAL

No implementation authority has been granted.

No source or test mutation is authorized by this request.

---

## 3. Historical / Archive Observation

Historical/archive inspection recorded a mismatch between the archived Evidence Matrix EM-003 note and an archived verifier expectation.

The archived Evidence Matrix represented EM-003 as PARTIAL with the note:

> Found some evidence for deterministic/replayable, but more specific references needed for full coverage.

The archived verifier expectation was observed as:

> MISSING | Need exact file and line references showing deterministic/replayable requirements.

This historical mismatch was valid to document as an archive/snapshot governance observation.

---

## 4. Live Branch Observation

Later live-branch inspection showed that the active verifier checks for the PARTIAL EM-003 fragment:

> PARTIAL | Found some evidence for deterministic/replayable, but more specific references needed for full coverage.

Therefore, an active live-branch verifier/matrix mismatch is not currently proven.

The historical/archive mismatch remains documented, but it must not be treated as proof of a current live mismatch without revalidation.

---

## 5. Requested Decision

This request asks for a separate approval decision selecting one authorized EM-003 alignment path, if any future mutation is required.

The approver must explicitly choose one of the following options before any mutation occurs.

### Option A: Verifier-To-Matrix Alignment

Authorize a narrow verifier update so that verifier expectations match the authoritative Evidence Matrix text.

Allowed mutation target:

- `scripts/verify_slice_1_0_governance_repair.ps1`

Not authorized:

- source changes
- test changes unless separately approved
- Evidence Matrix status upgrade
- EM-003 completion
- Slice unblocking

### Option B: Matrix-To-Verifier Alignment

Authorize a narrow Evidence Matrix update so that the EM-003 wording matches the authoritative verifier expectation.

Allowed mutation target:

- `slice_1_0_evidence_matrix.md`
- or the repo-authoritative Evidence Matrix path, if different

Not authorized:

- source changes
- test changes unless separately approved
- verifier rewrite
- EM-003 completion unless line-grounded evidence is separately approved
- Slice unblocking

### Option C: Structured Verification Replacement

Authorize replacement of brittle full-text coupling with a structured EM-003-specific verification approach.

Allowed mutation target:

- `scripts/verify_slice_1_0_governance_repair.ps1`
- supporting governance documentation required to define the structured check

Not authorized:

- source changes
- runtime behavior changes
- broad verifier rewrite outside EM-003 scope
- EM-003 completion
- Slice unblocking

---

## 6. Recommended Default

Recommended decision: NO MUTATION UNTIL REVALIDATION.

Because live-branch inspection currently indicates alignment between the active verifier and the EM-003 PARTIAL note, no immediate verifier or Evidence Matrix mutation should occur unless a fresh line-grounded revalidation proves an active mismatch.

If revalidation proves no active mismatch, this request should be closed without mutation.

If revalidation proves an active mismatch, one and only one of Option A, Option B, or Option C must be explicitly approved before mutation.

---

## 7. Required Evidence Before Approval

Before approving any mutation path, the reviewer must provide line-grounded evidence for:

- the authoritative Evidence Matrix path
- the current EM-003 row or note
- the current verifier assertion for EM-003
- the exact mismatch, if one exists
- the selected mutation target
- why the selected option is the narrowest safe repair

Approval must not rely on stale archive-only evidence if live-branch files differ.

---

## 8. Explicit Non-Authorizations

This request does not authorize:

- modifying `src/`
- modifying `tests/`
- changing runtime behavior
- changing trading, risk, ML, reporting, or UI behavior
- marking EM-003 as COMPLETE
- changing Slice Status from BLOCKED
- changing Implementation Authority from NONE
- changing Approval Status from NOT APPROVED
- broad verifier rewrite
- broad Evidence Matrix rewrite
- package rename
- module move
- target architecture migration
- selecting Option A, B, or C without recorded approval

---

## 9. Approval Requirements

A valid approval must explicitly state:

- selected option: A, B, C, or NO MUTATION
- authorized file path or paths
- maximum allowed scope
- whether tests may be changed
- whether verifier may be changed
- whether Evidence Matrix may be changed
- confirmation that Slice Status remains BLOCKED
- confirmation that Implementation Authority remains NONE unless separately changed
- confirmation that EM-003 remains PARTIAL unless separately approved with line-grounded evidence

Without this explicit approval, no mutation is authorized.

---

## 10. Final Request State

Decision Requested: YES  
Decision Granted By This Document: NO  
Implementation Authority Granted: NO  
Source Changes Authorized: NO  
Test Changes Authorized: NO  
Verifier Changes Authorized: NO  
Evidence Matrix Changes Authorized: NO  
EM-003 Completion Authorized: NO  
Slice Unblocking Authorized: NO  

Current Slice Status: BLOCKED  
Current Implementation Authority: NONE  
Current Approval Status: NOT APPROVED  
Current EM-003 Status: PARTIAL
