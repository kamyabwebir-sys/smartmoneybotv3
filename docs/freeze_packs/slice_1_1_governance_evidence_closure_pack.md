# Slice 1.1 — Governance Evidence Closure Pack

Slice Status: PROPOSED
Implementation Authority: NONE
Approval Status: NOT APPROVED

## 1. Purpose

Slice 1.1 is a documentation-only and governance-only closure slice.

Its purpose is to close remaining governance ambiguity after Slice 1.0 by:

1. confirming the authoritative paths for Slice 1.0 governance artifacts,
2. aligning the governance verifier with the authoritative Evidence Matrix,
3. closing or explicitly documenting remaining evidence gaps for EM-003 and EM-013,
4. preserving Slice 1.0 blocked status until review evidence is sufficient.

This slice does not authorize implementation work.

## 2. Authority

Implementation Authority: NONE

This slice does not permit:

- code changes under `src/`
- test changes under `tests/`
- execution or trading logic
- risk calculation
- ML decisioning
- reporting/UI leakage into core/domain logic
- package rename
- module move
- broad refactor
- behavior changes to DiscoveryRegistry
- changes to Slice 0.10 contracts

## 3. Authoritative Files

The following files are authoritative for Slice 1.1 governance closure:

- `docs/freeze_packs/slice_1_0_freeze_pack.md`
- `docs/freeze_packs/slice_1_0_evidence_matrix.md`
- `docs/reviews/slice_1_0_governance_repair_review.md`
- `scripts/verify_slice_1_0_governance_repair.ps1`

If root-level copies exist, their role must be explicitly classified as one of:

- mirror copy
- convenience copy
- stale/non-authoritative copy

No duplicate source of truth is allowed.

## 4. Current Governance Baseline

Slice 1.0 remains blocked.

Expected baseline:

- Slice Status: BLOCKED
- Implementation Authority: NONE
- Approval Status: BLOCKED or NOT APPROVED according to the specific artifact semantics

Evidence Matrix current baseline:

- EM-003: PARTIAL
- EM-013: MISSING

## 5. EM-003 Closure Requirement

EM-003 currently has partial evidence for deterministic/replayable requirements.

To close EM-003, the Evidence Matrix must include exact file and line references showing:

1. deterministic structure discovery expectations,
2. replayability expectations,
3. no nondeterministic behavior,
4. no hidden external dependency,
5. stable/canonical behavior where relevant.

Acceptable evidence may reference documentation, tests, and current registry constraints, but this slice must not change implementation.

## 6. EM-013 Closure Requirement

EM-013 currently remains missing.

To close EM-013, the Evidence Matrix must include exact file and line references showing:

1. separation between governance/core/domain logic and reporting/UI concerns,
2. explicit exclusion of user-facing/reporting fields from core/domain behavior,
3. no approval for reporting leakage into discovery or registry behavior.

This slice must not add reporting behavior.

## 7. Verifier Requirements

The governance verifier must validate the authoritative matrix and freeze pack.

Verifier must assert:

- Slice Status remains BLOCKED
- Implementation Authority remains NONE
- Approval Status remains blocked/not approved according to artifact semantics
- EM-003 status matches the authoritative Evidence Matrix
- EM-013 status matches the authoritative Evidence Matrix
- no `src/` changes are present
- no `tests/` changes are present
- review note does not approve implementation

If EM-003 is PARTIAL in the authoritative matrix, the verifier must not assert MISSING for EM-003.

## 8. Allowed Changes

Only the following changes are allowed:

- documentation updates to governance artifacts
- evidence matrix line-reference completion
- verifier alignment with authoritative governance artifacts
- review note update preserving no-implementation authority

## 9. Disallowed Changes

The following are prohibited:

- changes under `src/`
- changes under `tests/`
- changes to package structure
- module moves
- broad refactor
- implementation logic
- execution/trading logic
- risk calculation
- ML decisioning
- reporting/UI behavior
- changes to DiscoveryRegistry behavior
- changes to Slice 0.10 authority

## 10. Exit Criteria

Slice 1.1 may be considered complete only if:

1. authoritative file paths are explicitly resolved,
2. EM-003 is either upgraded with exact references or explicitly remains PARTIAL with reason,
3. EM-013 is either upgraded with exact references or explicitly remains MISSING with reason,
4. verifier passes against the authoritative files,
5. git working tree is clean,
6. no `src/` or `tests/` changes are present,
7. review note preserves Implementation Authority: NONE.

## 11. Expected Final State

Expected final state is one of:

### Option A — Governance Closed but Still Blocked

- Slice Status: BLOCKED
- Implementation Authority: NONE
- Evidence gaps fully documented
- Ready for separate approval review

### Option B — Governance Still Blocked with Explicit Gaps

- Slice Status: BLOCKED
- Implementation Authority: NONE
- Remaining gaps listed deterministically
- No implementation authority granted
