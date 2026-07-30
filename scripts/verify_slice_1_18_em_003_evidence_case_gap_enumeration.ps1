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
