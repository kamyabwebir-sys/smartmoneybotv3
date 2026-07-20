# Slice 1.2 — Evidence Line Reference Repair Freeze Pack

Status: PROPOSED
Change Authority: DOCUMENTATION-ONLY
Implementation Authority: NONE
Approval Status: PENDING REVIEW

## 1. Purpose

Slice 1.2 is a narrow governance-only repair slice.

Its sole purpose is to add precise, repository-grounded line references
for EM-003 and EM-013 in the Slice 1.0 evidence matrix.

This slice does not authorize implementation work and does not unblock
Slice 1.0.

## 2. Authoritative Target

The only evidence-matrix target authorized for later repair under this
pack is:

- `docs/freeze_packs/slice_1_0_evidence_matrix.md`

The only matrix entries in scope are:

- `EM-003`
- `EM-013`

## 3. In Scope

The following changes are in scope:

1. Record exact line references for deterministic and replayable
   repository constraints supporting EM-003.
2. Record exact line references for the separation of Core from
   Reporting/UI concerns supporting EM-013.
3. Modify only the evidence-source, status, gap, or impact cells of
   EM-003 and EM-013 when justified by reviewed evidence.
4. Preserve the original meaning of both evidence requirements.
5. Keep all changes documentation-only, narrow, reviewable, and
   deterministic.

## 4. Candidate Evidence for EM-003

Candidate documentation evidence includes:

- `docs/core_contracts_principles.md:12-14`
- `docs/deterministic_assumptions_v1.md:8-13`
- `docs/testing_strategy.md:11-19`
- `docs/core_contract_semantics_v1.md:17-27`
- `docs/core_contract_semantics_v1.md:377-384`
- `docs/roadmap.md:5`
- `docs/roadmap.md:13-22`
- `docs/architecture_boundaries.md:7-12`

Candidate implementation or test evidence already referenced by the
matrix may be retained only if its exact line reference is verified
against the current repository revision.

Candidate references are not automatically accepted evidence. Each
reference must be reviewed against the exact claim made by EM-003.

## 5. Candidate Evidence for EM-013

Candidate documentation evidence includes:

- `docs/architecture_boundaries.md:5-23`
- `docs/deterministic_assumptions_v1.md:13-23`
- `docs/roadmap.md:35`
- `docs/roadmap.md:128`
- `docs/roadmap.md:197-211`
- `docs/slice_0_6_domain_contracts.md:24-30`

Repository inspection may be recorded as supplementary evidence only.
The absence of reporting/UI search matches in source files must not be
treated as proof beyond the exact inspected paths and patterns.

Candidate references are not automatically accepted evidence. Each
reference must be reviewed against the exact claim made by EM-013.

## 6. Explicit Exclusions

This slice must not:

- modify any file under `src/`;
- modify any file under `tests/`;
- add or change runtime behavior;
- introduce domain contracts;
- introduce reporting or UI fields into Core or Domain contracts;
- rename packages or move modules;
- create future target-architecture package trees;
- perform a broad documentation refactor;
- authorize execution or trading logic;
- authorize risk calculation;
- authorize opaque ML decisioning;
- change Slice 1.0 implementation authority;
- change Slice 1.0 from BLOCKED to unblocked;
- claim implementation completion.

## 7. Status Discipline

The following Slice 1.0 governance declarations remain unchanged:

- `Status: BLOCKED`
- `Implementation Authority: NONE`
- `Approval Status: BLOCKED`

A repaired evidence reference does not, by itself, grant implementation
authority or approve Slice 1.0.

## 8. Evidence Repair Rules

For each repaired matrix entry:

1. The referenced file must exist in the current repository.
2. The referenced line or line range must contain evidence relevant to
   the exact matrix claim.
3. References must use repository-relative paths.
4. Status changes must be justified by the complete evidence set.
5. `MISSING` must not become `VERIFIED` merely because one related
   statement exists.
6. `PARTIAL` must not become `VERIFIED` unless the full claim is
   demonstrably covered.
7. Unresolved gaps must remain explicit.
8. Evidence must not rely on unstated architectural intent.

## 9. Allowed Files

The maximum allowed change set for this slice is:

- `docs/freeze_packs/slice_1_2_evidence_line_reference_repair_pack.md`
- `docs/freeze_packs/slice_1_0_evidence_matrix.md`

The freeze-pack file should be committed separately before any
evidence-matrix repair unless governance review explicitly approves a
single combined commit.

## 10. Exit Criteria

Slice 1.2 may be considered complete only when:

1. This freeze pack exists and has been reviewed.
2. EM-003 contains exact and verified repository line references.
3. EM-013 contains exact and verified repository line references.
4. Any status changes are supported by the full referenced evidence.
5. No files under `src/` or `tests/` have changed.
6. Slice 1.0 remains BLOCKED.
7. Slice 1.0 implementation authority remains NONE.
8. The final Git diff contains only authorized documentation files.
9. The working tree is clean after the approved commit or commits.

## 11. Review Commands

Review must include:
```powershell
git status --short
git diff --check
git diff --name-only
git diff -- docs/freeze_packs/slice_1_2_evidence_line_reference_repair_pack.md
git diff -- docs/freeze_packs/slice_1_0_evidence_matrix.md

Before committing the evidence-matrix repair, verify that no source or
test files changed:

powershell
$Forbidden = git diff --name-only |
Where-Object { $_ -match '^(src|tests)/' }

if ($Forbidden) {
$Forbidden
throw "Slice 1.2 violation: src/ or tests/ changes detected."
}

## 12. Governance Result

This pack authorizes documentation review and evidence-line-reference
repair only.

It grants no implementation authority and does not unblock Slice 1.0.
