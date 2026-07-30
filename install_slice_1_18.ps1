$ErrorActionPreference = "Stop"

$FreezeDir = "docs/freeze_packs"
$ReviewDir = "docs/reviews"
$ScriptsDir = "scripts"

New-Item -ItemType Directory -Force -Path $FreezeDir | Out-Null
New-Item -ItemType Directory -Force -Path $ReviewDir | Out-Null
New-Item -ItemType Directory -Force -Path $ScriptsDir | Out-Null

$FreezePackPath = Join-Path $FreezeDir "slice_1_18_em_003_evidence_case_gap_enumeration.md"
$ReviewPath = Join-Path $ReviewDir "slice_1_18_em_003_evidence_case_gap_enumeration_review.md"
$VerifierPath = Join-Path $ScriptsDir "verify_slice_1_18_em_003_evidence_case_gap_enumeration.ps1"

@'
# Slice 1.18 - EM-003 Evidence Case Gap Enumeration

## Governance Status

Slice: 1.18
Mode: governance-only
Subject: EM-003 Evidence Case Gap Enumeration
EM-003 Status: PARTIAL
Promotion Gate: LOCKED
Implementation Authority: NOT GRANTED
Promotion Authority: NOT GRANTED
Verifier Authority: evidence-gap enumeration only

## Source Locks

This slice is bound by the previously locked EM-003 governance artifacts:

- Slice 1.5: acceptance criteria lock
- Slice 1.6: verifier case matrix lock
- Slice 1.7: evidence report shape lock
- Slice 1.8: promotion gate lock
- Slice 1.14: limited verifier authority grant

This slice does not override, relax, reinterpret, or promote any prior lock.

## Purpose

Enumerate evidence gaps for EM003-CASE-001 through EM003-CASE-010 so later implementation or verifier work can be scoped narrowly and reviewed separately.

This slice records gaps only. It does not populate evidence, execute verifier logic, modify tests, modify source code, or grant authority for EM-003 promotion.

## Case Gap Enumeration

| Case ID | Locked Criterion | Current Evidence Position | Gap Status | Required Future Evidence |
|---|---|---|---|---|
| EM003-CASE-001 | Canonical serialization stability | Evidence is not fully grounded for final promotion. | GAP | Direct verifier evidence proving stable canonical serialization across replay runs. |
| EM003-CASE-002 | Deterministic ordering | Evidence is not fully grounded for final promotion. | GAP | Direct verifier evidence proving stable ordering independent of input traversal or runtime ordering artifacts. |
| EM003-CASE-003 | No wall-clock dependency | Evidence is not fully grounded for final promotion. | GAP | Direct verifier evidence proving replay output does not depend on wall-clock time. |
| EM003-CASE-004 | No randomness dependency | Evidence is not fully grounded for final promotion. | GAP | Direct verifier evidence proving replay output does not depend on randomness, seeds, or nondeterministic entropy. |
| EM003-CASE-005 | Stable identifiers | Evidence is not fully grounded for final promotion. | GAP | Direct verifier evidence proving identifiers are stable for the same canonical inputs. |
| EM003-CASE-006 | Stable error surface | Evidence is not fully grounded for final promotion. | GAP | Direct verifier evidence proving deterministic error codes, error shape, and failure classification. |
| EM003-CASE-007 | Manifest completeness | Manifest coverage is insufficient for final promotion. | CRITICAL_GAP | Complete manifest evidence with required fields, stable references, and traceable attachment coverage. |
| EM003-CASE-008 | Environment isolation | Evidence is not fully grounded for final promotion. | GAP | Direct verifier evidence proving environment variables, filesystem state, locale, timezone, and host-specific state do not affect replay result. |
| EM003-CASE-009 | Golden replay consistency | Golden replay evidence is insufficient for final promotion. | CRITICAL_GAP | Golden replay evidence proving repeatable identical outputs from fixed inputs and fixed manifests. |
| EM003-CASE-010 | Evidence traceability | Evidence traceability is not fully grounded for final promotion. | GAP | Direct verifier evidence linking each case to attachments, manifests, reports, and reviewable provenance. |

## Locked Outcomes

The only allowed outcome of this slice is a governance gap inventory.

The following outcomes are explicitly forbidden:

- Changing EM-003 status from PARTIAL to GROUNDED
- Unlocking the Promotion Gate
- Granting implementation authority
- Granting promotion authority
- Modifying src/
- Modifying tests/
- Modifying registry logic
- Modifying replay engine logic
- Treating this gap enumeration as evidence population
- Treating this slice as verifier PASS authority

## Promotion Position

EM-003 remains PARTIAL.

Promotion remains LOCKED.

Any future promotion requires a separate slice with direct evidence population, verifier execution evidence, deterministic replay confirmation, and explicit review approval.
'@ | Set-Content -Path $FreezePackPath -Encoding utf8NoBOM

@'
# Slice 1.18 Review - EM-003 Evidence Case Gap Enumeration

## Review Verdict

Verdict: PASS
Review Mode: governance-only
EM-003 Status After Review: PARTIAL
Promotion Gate After Review: LOCKED
Implementation Authority Granted: NO
Promotion Authority Granted: NO

## Review Scope

This review covers only the governance validity of the Slice 1.18 evidence case gap enumeration.

The review confirms that Slice 1.18:

- Enumerates EM003-CASE-001 through EM003-CASE-010
- Preserves the locked verifier case matrix
- Preserves EM-003 as PARTIAL
- Preserves the Promotion Gate as LOCKED
- Grants no implementation authority
- Grants no promotion authority
- Does not authorize source, test, registry, or replay engine changes

## Findings

### Finding 1 - Scope Is Governance-Only

Slice 1.18 is limited to evidence gap enumeration.

No execution logic, trading logic, risk calculation, opaque ML decisioning, reporting leakage, or core/domain behavior change is introduced.

Status: PASS

### Finding 2 - Promotion Remains Locked

The slice does not promote EM-003 and does not create a promotion path by implication.

EM-003 remains PARTIAL until a later separately approved slice provides complete direct evidence and receives explicit promotion approval.

Status: PASS

### Finding 3 - Critical Gaps Are Explicit

EM003-CASE-007 and EM003-CASE-009 are marked CRITICAL_GAP because manifest completeness and golden replay consistency are required for deterministic replayable grounding.

Status: PASS

### Finding 4 - Authority Boundaries Are Preserved

Verifier authority remains limited to evidence-gap enumeration for this slice.

The slice grants no autonomous implementation authority and no autonomous promotion authority.

Status: PASS

## Final Review Position

Slice 1.18 is accepted as a governance-only gap enumeration artifact.

It must not be used as proof of EM-003 completion, verifier PASS, promotion readiness, implementation permission, or promotion authorization.
'@ | Set-Content -Path $ReviewPath -Encoding utf8NoBOM

@'
$ErrorActionPreference = "Stop"

$FreezePack = "docs/freeze_packs/slice_1_18_em_003_evidence_case_gap_enumeration.md"
$Review = "docs/reviews/slice_1_18_em_003_evidence_case_gap_enumeration_review.md"

if (-not (Test-Path $FreezePack)) {
    throw "Missing freeze pack: $FreezePack"
}

if (-not (Test-Path $Review)) {
    throw "Missing review: $Review"
}

$FreezeText = Get-Content $FreezePack -Raw
$ReviewText = Get-Content $Review -Raw
$Combined = $FreezeText + "`n" + $ReviewText

$RequiredTerms = @(
    "Mode: governance-only",
    "EM-003 Status: PARTIAL",
    "Promotion Gate: LOCKED",
    "Implementation Authority: NOT GRANTED",
    "Promotion Authority: NOT GRANTED",
    "EM003-CASE-001",
    "EM003-CASE-002",
    "EM003-CASE-003",
    "EM003-CASE-004",
    "EM003-CASE-005",
    "EM003-CASE-006",
    "EM003-CASE-007",
    "EM003-CASE-008",
    "EM003-CASE-009",
    "EM003-CASE-010",
    "CRITICAL_GAP"
)

foreach ($Term in $RequiredTerms) {
    if ($Combined -notlike "*$Term*") {
        throw "Missing required governance term: $Term"
    }
}

$ForbiddenExactTerms = @(
    "EM-003 Status: GROUNDED",
    "Promotion Gate: UNLOCKED",
    "Implementation Authority: GRANTED",
    "Promotion Authority: GRANTED",
    "Implementation Authority Granted: YES",
    "Promotion Authority Granted: YES",
    "Verifier PASS authority: GRANTED",
    "Promotion approved",
    "EM-003 promoted"
)

foreach ($Term in $ForbiddenExactTerms) {
    if ($Combined -like "*$Term*") {
        throw "Forbidden governance term found: $Term"
    }
}

$RequiredDenials = @(
    "Implementation Authority: NOT GRANTED",
    "Promotion Authority: NOT GRANTED",
    "Implementation Authority Granted: NO",
    "Promotion Authority Granted: NO",
    "EM-003 remains PARTIAL",
    "Promotion remains LOCKED"
)

foreach ($Term in $RequiredDenials) {
    if ($Combined -notlike "*$Term*") {
        throw "Missing required authority denial: $Term"
    }
}

$CaseMatches = [regex]::Matches($FreezeText, "EM003-CASE-0\d\d")
$UniqueCases = $CaseMatches.Value | Sort-Object -Unique

if ($UniqueCases.Count -ne 10) {
    throw "Expected 10 unique EM003 cases in freeze pack, found $($UniqueCases.Count): $($UniqueCases -join ', ')"
}

foreach ($CaseNumber in 1..10) {
    $CaseId = "EM003-CASE-{0:D3}" -f $CaseNumber
    if ($UniqueCases -notcontains $CaseId) {
        throw "Missing case id in freeze pack: $CaseId"
    }
}

$CriticalGapCount = ([regex]::Matches($FreezeText, "\bCRITICAL_GAP\b")).Count
if ($CriticalGapCount -lt 2) {
    throw "Expected at least two CRITICAL_GAP entries for manifest completeness and golden replay consistency."
}

Write-Host "PASS: Slice 1.18 EM-003 evidence case gap enumeration is governance-only, fail-closed, and promotion-locked."
'@ | Set-Content -Path $VerifierPath -Encoding utf8NoBOM

Write-Host "Installed Slice 1.18 governance artifacts:"
Write-Host " - $FreezePackPath"
Write-Host " - $ReviewPath"
Write-Host " - $VerifierPath"

& $VerifierPath
