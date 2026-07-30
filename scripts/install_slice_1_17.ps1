$ErrorActionPreference = "Stop"

function Write-FileUtf8NoBom($Path, $Content) {
    $Directory = Split-Path -Parent $Path
    if ($Directory -and -not (Test-Path $Directory)) {
        New-Item -ItemType Directory -Force -Path $Directory | Out-Null
    }

    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $Utf8NoBom)
}

$FreezePackPath = "docs/freeze_packs/slice_1_17_em_003_separate_promotion_authority_request_gate.md"
$ReviewPath = "docs/reviews/slice_1_17_em_003_separate_promotion_authority_request_gate_review.md"
$VerifierPath = "scripts/verify_slice_1_17_em_003_separate_promotion_authority_request_gate.ps1"

$FreezePackContent = @'
# Slice 1.17 - EM-003 Separate Promotion Authority Request Gate

## Status

PROPOSED

## Slice Type

Governance-only authority request gate.

## Purpose

Slice 1.17 defines a deterministic, replayable, fail-closed governance gate for evaluating whether EM-003 is ready to request separate human promotion authority.

This slice does not promote EM-003.

This slice does not unlock the EM-003 promotion gate.

This slice does not grant implementation authority.

This slice does not modify source code, tests, protected registry files, or runtime behavior.

## Current Authoritative Position

EM-003 remains PARTIAL.

Promotion remains LOCKED.

Implementation authority remains NONE.

Approval status remains NOT_APPROVED.

The current known evidence artifact is not sufficient for a separate promotion authority request because the evidence case population is empty or incomplete.

## Governance Background

Slice 1.14 granted limited future implementation authority to Slice 1.15 only.

That limited authority does not transfer to Slice 1.17.

Slice 1.17 may only evaluate request-readiness under governance-only constraints.

Any future promotion requires a separate explicit approved authority action.

## Inputs

The Slice 1.17 gate may read the following governance and evidence materials:

- artifacts/discovery/em003/evidence_report.json
- artifacts/discovery/em003/attachment_register.json, if present
- docs/freeze_packs/slice_1_5_em_003_acceptance_criteria_lock.md
- docs/freeze_packs/slice_1_6_em_003_verifier_case_matrix_lock.md
- docs/freeze_packs/slice_1_7_em_003_evidence_report_shape_lock.md
- docs/freeze_packs/slice_1_8_em_003_promotion_gate_lock.md
- docs/freeze_packs/slice_1_14_em_003_limited_verifier_authority_grant.md
- docs/reviews/slice_1_14_em_003_authority_grant_review.md
- docs/reviews/slice_1_16_em_003_evidence_result_adjudication_review.md, if present

## Allowed Actions

Slice 1.17 may:

- read locked governance materials
- read generated EM-003 evidence artifacts
- classify whether a separate authority request is blocked or request-ready
- produce a governance-only review
- produce a governance-only verifier script
- fail closed on missing, ambiguous, partial, contradictory, or unauthorized evidence state

## Forbidden Actions

Slice 1.17 must not:

- modify files under src/
- modify files under tests/
- modify protected registry files
- change EM-003 status
- unlock the EM-003 promotion gate
- grant implementation authority
- approve EM-003
- reinterpret indirect evidence as direct evidence
- introduce execution logic
- introduce trading logic
- introduce risk calculation
- introduce opaque ML decisioning
- leak reporting or UI concerns into core or domain logic

## Protected Paths

The following paths remain protected and must not be modified by this slice:

- src/smart_money/discovery/registry.py
- tests/discovery/test_registry.py

In addition, Slice 1.17 must not modify any path under:

- src/
- tests/

## Deterministic Verdicts

The Slice 1.17 review must contain exactly one of the following verdicts:

- AUTHORITY_REQUEST_DENIED_FAIL_CLOSED
- AUTHORITY_REQUEST_READY_FOR_SEPARATE_HUMAN_APPROVAL

Neither verdict changes EM-003 status.

Neither verdict unlocks the promotion gate.

Neither verdict grants implementation authority.

## Decision Rules

The verdict must be AUTHORITY_REQUEST_DENIED_FAIL_CLOSED if any of the following conditions are true:

- evidence_report.json is missing
- evidence_report.json is not valid JSON
- evidence_report.json em_id is not EM-003
- evidence_report.json status is not PARTIAL
- evidence_report.json promotion_gate is not LOCKED
- evidence_report.json implementation_authority is not NONE
- evidence_report.json approval_status is not NOT_APPROVED
- evidence_report.json cases is missing
- evidence_report.json cases is empty
- any required verifier case is missing
- any required verifier case is partial
- any required governance mapping is missing
- deterministic evidence is missing or false
- replayable evidence is missing or false
- the review fails to state governance-only
- the review fails to state EM-003 remains PARTIAL
- the review fails to state Promotion remains blocked or Promotion remains LOCKED
- unauthorized source, test, or protected registry changes are present
- ambiguous approval or promotion language is present

The verdict may be AUTHORITY_REQUEST_READY_FOR_SEPARATE_HUMAN_APPROVAL only if all locked governance conditions are satisfied, all required cases are present, all required cases are non-partial, deterministic and replayable evidence is complete, and the result remains governance-only.

## Current Expected Verdict

Given the current known evidence posture, the expected verdict is:

AUTHORITY_REQUEST_DENIED_FAIL_CLOSED

Rationale:

- EM-003 remains PARTIAL.
- Promotion remains LOCKED.
- Implementation authority remains NONE.
- Approval status remains NOT_APPROVED.
- Evidence case population is empty or incomplete.

## Acceptance Criteria

Slice 1.17 is accepted only if:

- the freeze pack exists
- the review exists
- the verifier script exists
- the review explicitly states governance-only
- the review explicitly states EM-003 remains PARTIAL
- the review explicitly states Promotion remains blocked or Promotion remains LOCKED
- the review contains exactly one allowed deterministic verdict
- the verifier fails closed on missing evidence_report.json
- the verifier fails closed on invalid evidence_report.json
- the verifier fails closed on any non-PARTIAL EM-003 status
- the verifier fails closed on any unlocked promotion gate
- the verifier fails closed on any implementation authority other than NONE
- the verifier fails closed on any approval status other than NOT_APPROVED
- the verifier fails closed when evidence cases are empty unless the review verdict is AUTHORITY_REQUEST_DENIED_FAIL_CLOSED

## Final Governance Position

Slice 1.17 is a request-readiness gate only.

Separate authority request readiness is not promotion.

EM-003 remains PARTIAL.

Promotion remains blocked.

Any future promotion requires a distinct, explicit, separately approved authority action.
'@

$ReviewContent = @'
# Slice 1.17 - EM-003 Separate Promotion Authority Request Gate Review

## Review Status

PASS_WITH_REQUEST_DENIED_FAIL_CLOSED

## Scope Review

This review evaluates whether EM-003 is ready to request separate human promotion authority.

This review is governance-only.

This review does not promote EM-003.

This review does not unlock the promotion gate.

This review does not grant implementation authority.

This review does not modify implementation code, tests, protected registry files, or runtime behavior.

## Evidence Inputs Reviewed

- artifacts/discovery/em003/evidence_report.json
- artifacts/discovery/em003/attachment_register.json, if present
- Slice 1.5 acceptance criteria lock
- Slice 1.6 verifier case matrix lock
- Slice 1.7 evidence report shape lock
- Slice 1.8 promotion gate lock
- Slice 1.14 limited verifier authority grant
- Slice 1.16 adjudication review, if present

## Current EM-003 Status

EM-003 remains PARTIAL.

Promotion remains LOCKED.

Implementation authority remains NONE.

Approval status remains NOT_APPROVED.

## Verdict

AUTHORITY_REQUEST_DENIED_FAIL_CLOSED

## Rationale

The current evidence artifact preserves PARTIAL status and LOCKED promotion posture.

The current evidence artifact does not establish approval.

The current evidence artifact does not establish implementation authority.

The current evidence artifact does not provide completed verifier case population sufficient for a separate promotion authority request.

The current evidence case population is empty or incomplete.

Because the required deterministic and replayable direct evidence population is not complete, the authority request must remain denied under fail-closed governance.

## Guardrail Confirmation

- governance-only
- no src/ changes
- no tests/ changes
- no protected registry changes
- status remains unchanged
- promotion is not performed
- implementation authority remains NONE
- promotion gate remains LOCKED
- no execution logic introduced
- no trading logic introduced
- no risk calculation introduced
- no opaque ML decisioning introduced
- no reporting or UI leakage into core or domain logic

## Protected Path Confirmation

The following protected paths remain out of scope:

- src/smart_money/discovery/registry.py
- tests/discovery/test_registry.py

No Slice 1.17 action is authorized to modify these paths.

## Determinism and Replayability Review

The Slice 1.17 decision is deterministic because it is derived only from locked governance artifacts and the current EM-003 evidence report.

The Slice 1.17 decision is replayable because the same evidence report fields and locked governance inputs produce the same verdict.

Current deterministic verdict:

AUTHORITY_REQUEST_DENIED_FAIL_CLOSED

## Final Position

EM-003 remains PARTIAL.

Promotion remains blocked.

The separate authority request is denied fail-closed for this slice.

A future authority request may be reconsidered only after deterministic, replayable, complete, and properly populated evidence is available under separately approved governance scope.
'@

$VerifierContent = @'
$ErrorActionPreference = "Stop"

function Fail($Message) {
    Write-Host "FAIL-CLOSED: $Message" -ForegroundColor Red
    exit 1
}

function Pass($Message) {
    Write-Host "PASS: $Message" -ForegroundColor Green
}

function Normalize-PathForGovernance($Path) {
    return ($Path -replace "\\", "/").Trim()
}

$FreezePackPath = "docs/freeze_packs/slice_1_17_em_003_separate_promotion_authority_request_gate.md"
$ReviewPath = "docs/reviews/slice_1_17_em_003_separate_promotion_authority_request_gate_review.md"
$EvidenceReportPath = "artifacts/discovery/em003/evidence_report.json"

if (-not (Test-Path $FreezePackPath)) {
    Fail "Missing Slice 1.17 freeze pack: $FreezePackPath"
}

if (-not (Test-Path $ReviewPath)) {
    Fail "Missing Slice 1.17 review: $ReviewPath"
}

if (-not (Test-Path $EvidenceReportPath)) {
    Fail "Missing EM-003 evidence report: $EvidenceReportPath"
}

$FreezePack = Get-Content $FreezePackPath -Raw
$Review = Get-Content $ReviewPath -Raw
$EvidenceReportRaw = Get-Content $EvidenceReportPath -Raw

try {
    $EvidenceReport = $EvidenceReportRaw | ConvertFrom-Json
} catch {
    Fail "evidence_report.json is not valid JSON."
}

if ($EvidenceReport.em_id -ne "EM-003") {
    Fail "Unexpected em_id. Expected EM-003, found: $($EvidenceReport.em_id)"
}

if ($EvidenceReport.status -ne "PARTIAL") {
    Fail "EM-003 must remain PARTIAL. Found: $($EvidenceReport.status)"
}

if ($EvidenceReport.promotion_gate -ne "LOCKED") {
    Fail "Promotion gate must remain LOCKED. Found: $($EvidenceReport.promotion_gate)"
}

if ($EvidenceReport.implementation_authority -ne "NONE") {
    Fail "Implementation authority must remain NONE. Found: $($EvidenceReport.implementation_authority)"
}

if ($EvidenceReport.approval_status -ne "NOT_APPROVED") {
    Fail "Approval status must remain NOT_APPROVED. Found: $($EvidenceReport.approval_status)"
}

if ($null -eq $EvidenceReport.deterministic) {
    Fail "Evidence report must include deterministic field."
}

if ($EvidenceReport.deterministic -ne $true) {
    Fail "Evidence report deterministic field must be true for governance review."
}

if ($null -eq $EvidenceReport.replayable) {
    Fail "Evidence report must include replayable field."
}

if ($EvidenceReport.replayable -ne $true) {
    Fail "Evidence report replayable field must be true for governance review."
}

if ($FreezePack -notlike "*governance-only*") {
    Fail "Freeze pack must explicitly state governance-only."
}

if ($Review -notlike "*governance-only*") {
    Fail "Review must explicitly state governance-only."
}

if ($Review -notlike "*EM-003 remains PARTIAL*") {
    Fail "Review must explicitly state EM-003 remains PARTIAL."
}

if (($Review -notlike "*Promotion remains blocked*") -and ($Review -notlike "*Promotion remains LOCKED*")) {
    Fail "Review must explicitly preserve blocked or locked promotion posture."
}

if ($Review -notlike "*Implementation authority remains NONE*") {
    Fail "Review must explicitly state implementation authority remains NONE."
}

if ($Review -notlike "*Approval status remains NOT_APPROVED*") {
    Fail "Review must explicitly state approval status remains NOT_APPROVED."
}

$AllowedVerdicts = @(
    "AUTHORITY_REQUEST_DENIED_FAIL_CLOSED",
    "AUTHORITY_REQUEST_READY_FOR_SEPARATE_HUMAN_APPROVAL"
)

$VerdictMatches = @()
foreach ($Verdict in $AllowedVerdicts) {
    if ($Review -like "*$Verdict*") {
        $VerdictMatches += $Verdict
    }
}

if ($VerdictMatches.Count -ne 1) {
    Fail "Review must contain exactly one allowed authority request verdict."
}

$SelectedVerdict = $VerdictMatches[0]

$CasesMissingOrEmpty = $false

if ($null -eq $EvidenceReport.cases) {
    $CasesMissingOrEmpty = $true
} elseif ($EvidenceReport.cases.Count -eq 0) {
    $CasesMissingOrEmpty = $true
}

if ($CasesMissingOrEmpty -and $SelectedVerdict -ne "AUTHORITY_REQUEST_DENIED_FAIL_CLOSED") {
    Fail "Missing or empty case population requires AUTHORITY_REQUEST_DENIED_FAIL_CLOSED."
}

if ($CasesMissingOrEmpty -and $Review -notlike "*current evidence case population is empty or incomplete*") {
    Fail "Review must explain that current evidence case population is empty or incomplete."
}

if ($SelectedVerdict -eq "AUTHORITY_REQUEST_READY_FOR_SEPARATE_HUMAN_APPROVAL") {
    if ($CasesMissingOrEmpty) {
        Fail "Request-ready verdict is not allowed with missing or empty evidence cases."
    }

    foreach ($Case in $EvidenceReport.cases) {
        if ($null -eq $Case.case_id) {
            Fail "Every evidence case must include case_id for request-ready verdict."
        }

        if ($null -eq $Case.status) {
            Fail "Every evidence case must include status for request-ready verdict."
        }

        if ($Case.status -eq "PARTIAL") {
            Fail "Request-ready verdict is not allowed when any evidence case is PARTIAL."
        }

        if ($Case.status -eq "MISSING") {
            Fail "Request-ready verdict is not allowed when any evidence case is MISSING."
        }

        if ($Case.status -eq "FAILED") {
            Fail "Request-ready verdict is not allowed when any evidence case is FAILED."
        }
    }
}

$ForbiddenReviewPhrases = @(
    "approved promotion",
    "promotion granted",
    "authority granted",
    "gate unlocked",
    "status promoted",
    "status changed"
)

foreach ($Phrase in $ForbiddenReviewPhrases) {
    if ($Review -like "*$Phrase*") {
        Fail "Forbidden review phrase detected: $Phrase"
    }
}

$ForbiddenFreezePackPhrases = @(
    "approved promotion",
    "promotion granted",
    "authority granted",
    "gate unlocked",
    "status promoted",
    "status changed"
)

foreach ($Phrase in $ForbiddenFreezePackPhrases) {
    if ($FreezePack -like "*$Phrase*") {
        Fail "Forbidden freeze pack phrase detected: $Phrase"
    }
}

$ProtectedPaths = @(
    "src/smart_money/discovery/registry.py",
    "tests/discovery/test_registry.py"
)

$ForbiddenChangedPrefixes = @(
    "src/",
    "tests/"
)

$ChangedFiles = @()

try {
    $GitAvailable = $true
    git rev-parse --is-inside-work-tree *> $null
    if ($LASTEXITCODE -ne 0) {
        $GitAvailable = $false
    }

    if ($GitAvailable) {
        $ChangedFiles = git diff --name-only
        $StagedFiles = git diff --cached --name-only
        $UntrackedFiles = git ls-files --others --exclude-standard

        if ($null -ne $StagedFiles) {
            $ChangedFiles += $StagedFiles
        }

        if ($null -ne $UntrackedFiles) {
            $ChangedFiles += $UntrackedFiles
        }

        $ChangedFiles = $ChangedFiles | Where-Object { $_ -ne $null -and $_.Trim() -ne "" } | Sort-Object -Unique
    }
} catch {
    Write-Host "WARN: Git change inspection unavailable; continuing with artifact-level checks only." -ForegroundColor Yellow
    $ChangedFiles = @()
}

foreach ($Changed in $ChangedFiles) {
    $Normalized = Normalize-PathForGovernance $Changed

    foreach ($ProtectedPath in $ProtectedPaths) {
        if ($Normalized -eq $ProtectedPath) {
            Fail "Protected registry path change detected: $Normalized"
        }
    }

    foreach ($Prefix in $ForbiddenChangedPrefixes) {
        if ($Normalized.StartsWith($Prefix)) {
            Fail "Unauthorized src/tests change detected: $Normalized"
        }
    }
}

foreach ($Changed in $ChangedFiles) {
    $Normalized = Normalize-PathForGovernance $Changed

    if ($Normalized -like "docs/freeze_packs/slice_1_17_*") {
        continue
    }

    if ($Normalized -like "docs/reviews/slice_1_17_*") {
        continue
    }

    if ($Normalized -like "scripts/verify_slice_1_17_*") {
        continue
    }

    if ($Normalized -eq "scripts/install_slice_1_17.ps1") {
        continue
    }

    if ($Normalized.StartsWith("src/") -or $Normalized.StartsWith("tests/")) {
        Fail "Unauthorized implementation/test change detected: $Normalized"
    }
}

Pass "Slice 1.17 authority request gate remains governance-only, fail-closed, and PARTIAL-preserving."
'@

Write-FileUtf8NoBom $FreezePackPath $FreezePackContent
Write-FileUtf8NoBom $ReviewPath $ReviewContent
Write-FileUtf8NoBom $VerifierPath $VerifierContent

Write-Host "Wrote $FreezePackPath" -ForegroundColor Cyan
Write-Host "Wrote $ReviewPath" -ForegroundColor Cyan
Write-Host "Wrote $VerifierPath" -ForegroundColor Cyan

pwsh -NoProfile -ExecutionPolicy Bypass -File $VerifierPath
