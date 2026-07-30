$ErrorActionPreference = "Stop"

Write-Host "=== Slice 1.23 canonical manifest verification lock verifier ==="

$FreezePath = "docs/freeze_packs/slice_1_23_em_003_canonical_manifest_verification_lock.md"
$ReviewPath = "docs/reviews/slice_1_23_em_003_canonical_manifest_verification_lock_review.md"
$VerifierPath = "scripts/verify_slice_1_23_canonical_manifest_verification_lock.ps1"

function Assert-FileExists {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        throw "Required file missing: $Path"
    }
    Write-Host "[PASS] Exists: $Path"
}

function Assert-Contains {
    param(
        [string]$Content,
        [string]$Pattern,
        [string]$Message
    )
    if ($Content -notmatch [regex]::Escape($Pattern)) {
        throw "Missing required text: $Message :: $Pattern"
    }
    Write-Host "[PASS] $Message"
}

function Assert-NotContainsRegex {
    param(
        [string]$Content,
        [string]$Pattern,
        [string]$Message
    )
    if ($Content -match $Pattern) {
        throw "Forbidden text detected: $Message :: $Pattern"
    }
    Write-Host "[PASS] $Message"
}

Assert-FileExists $FreezePath
Assert-FileExists $ReviewPath
Assert-FileExists $VerifierPath

$Freeze = Get-Content -Raw -Path $FreezePath
$Review = Get-Content -Raw -Path $ReviewPath
$Combined = $Freeze + "`n" + $Review

Assert-Contains $Freeze "Mode: governance-only" "Freeze pack preserves governance-only mode"
Assert-Contains $Freeze "EM-003 Status: PARTIAL" "Freeze pack preserves EM-003 PARTIAL"
Assert-Contains $Freeze "Promotion Gate: LOCKED" "Freeze pack preserves Promotion Gate LOCKED"
Assert-Contains $Freeze "Canonical Manifest Verification Contract: LOCKED" "Freeze pack locks verification contract"

Assert-Contains $Freeze "Implementation Authority: NOT GRANTED" "Implementation authority denied"
Assert-Contains $Freeze "Promotion Authority: NOT GRANTED" "Promotion authority denied"
Assert-Contains $Freeze "Source Code Change Authority: NOT GRANTED" "Source-code change authority denied"
Assert-Contains $Freeze "Test Code Change Authority: NOT GRANTED" "Test-code change authority denied"
Assert-Contains $Freeze "Registry Change Authority: NOT GRANTED" "Registry change authority denied"
Assert-Contains $Freeze "Replay Engine Change Authority: NOT GRANTED" "Replay engine change authority denied"

Assert-Contains $Freeze "canonical serialization" "Canonical serialization verification objective present"
Assert-Contains $Freeze "deterministic ID generation" "Deterministic ID generation verification objective present"
Assert-Contains $Freeze "replay manifest behavior" "Replay manifest behavior verification objective present"
Assert-Contains $Freeze "fail-closed" "Fail-closed verification language present"

Assert-Contains $Review "Review Verdict: PASS" "Review verdict PASS"
Assert-Contains $Review "Review Mode: governance-only" "Review mode governance-only"
Assert-Contains $Review "EM-003 Status After Review: PARTIAL" "Review preserves EM-003 PARTIAL"
Assert-Contains $Review "Promotion Gate After Review: LOCKED" "Review preserves Promotion Gate LOCKED"
Assert-Contains $Review "Implementation Authority Granted: NO" "Review grants no implementation authority"
Assert-Contains $Review "Promotion Authority Granted: NO" "Review grants no promotion authority"

Assert-NotContainsRegex $Combined "Implementation Authority:\s*GRANTED" "No implementation authority granted"
Assert-NotContainsRegex $Combined "Promotion Authority:\s*GRANTED" "No promotion authority granted"
Assert-NotContainsRegex $Combined "Implementation Authority Granted:\s*YES" "No review implementation authority YES"
Assert-NotContainsRegex $Combined "Promotion Authority Granted:\s*YES" "No review promotion authority YES"
Assert-NotContainsRegex $Combined "EM-003 Status:\s*(COMPLETE|GROUNDED|PROMOTED)" "No EM-003 completion/promotion status"
Assert-NotContainsRegex $Combined "Promotion Gate:\s*UNLOCKED" "Promotion gate not unlocked"

$ForbiddenChangedPaths = @(
    "^src/",
    "^tests/",
    "^artifacts/",
    "^src\\",
    "^tests\\",
    "^artifacts\\"
)

$Changed = git status --short | ForEach-Object {
    if ($_ -match "^.. (?<path>.+)$") {
        $Matches["path"]
    }
}

foreach ($Path in $Changed) {
    foreach ($Forbidden in $ForbiddenChangedPaths) {
        if ($Path -match $Forbidden) {
            throw "Slice 1.23 is governance-only and forbids changed path: $Path"
        }
    }
}

Write-Host "[PASS] No forbidden src/tests/artifacts path changes detected."
Write-Host "=== Slice 1.23 governance verification PASS ==="
