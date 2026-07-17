$ErrorActionPreference = "Stop"

$matrix = "slice_1_0_evidence_matrix.md"
$freeze = "slice_1_0_freeze_pack.md"
$review = "docs/reviews/slice_1_0_governance_repair_review.md"

function Assert-FileExists {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing required file: $Path"
    }
}

function Assert-Pattern {
    param(
        [string]$Path,
        [string]$Pattern,
        [string]$Description
    )

    $match = Select-String -LiteralPath $Path -Pattern $Pattern -Quiet

    if (-not $match) {
        throw "Missing pattern in ${Path}: ${Description}"
    }
}

function Assert-NoSourceOrTestChanges {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Host "SKIP: git not found; cannot check source/test diff."
        return
    }

    $changed = git status --short

    foreach ($line in $changed) {
        $path = $line.Substring(3).Trim()

        if ($path -like "src/*" -or
            $path -like "src\*" -or
            $path -like "tests/*" -or
            $path -like "tests\*") {
            throw "Source/test change detected but not authorized: $path"
        }
    }
}

Assert-FileExists $matrix
Assert-FileExists $freeze
Assert-FileExists $review

# Evidence Matrix governance header must remain blocked / no authority / not approved.
Assert-Pattern $matrix '^Slice Status:\s*BLOCKED$' 'Slice Status must remain BLOCKED'
Assert-Pattern $matrix '^Implementation Authority:\s*NONE$' 'Implementation Authority must remain NONE'
Assert-Pattern $matrix '^Approval Status:\s*NOT APPROVED$' 'Approval Status must remain NOT APPROVED'

# Freeze Pack governance must remain blocked / no authority.
Assert-Pattern $freeze '^Status:\s*BLOCKED$' 'Freeze Pack status must remain BLOCKED'
Assert-Pattern $freeze '^Implementation Authority:\s*NONE$' 'Freeze Pack authority must remain NONE'
Assert-Pattern $freeze '^Approval Status:\s*BLOCKED$' 'Freeze Pack approval status must remain BLOCKED'
Assert-Pattern $freeze 'It does not approve source changes, test changes, package creation, module placement' 'Freeze Pack non-approval statement must remain present'
Assert-Pattern $freeze 'Final state remains BLOCKED until a separate approval review explicitly changes it\.' 'Freeze Pack final-state guardrail must remain present'

# Current observed Evidence Matrix row statuses.
# This verifier intentionally guards the current file state and does not upgrade EM rows.
Assert-Pattern $matrix '^\|\s*EM-002\s*\|.*\|\s*PARTIAL\s*\|' 'EM-002 must remain PARTIAL unless separately approved'
Assert-Pattern $matrix '^\|\s*EM-003\s*\|.*\|\s*MISSING\s*\|' 'EM-003 must remain MISSING unless separately repaired'
Assert-Pattern $matrix '^\|\s*EM-004\s*\|.*\|\s*MISSING\s*\|' 'EM-004 must remain MISSING unless separately repaired'
Assert-Pattern $matrix '^\|\s*EM-013\s*\|.*\|\s*MISSING\s*\|' 'EM-013 must remain MISSING unless separately repaired'
Assert-Pattern $matrix '^\|\s*EM-016\s*\|.*\|\s*MISSING\s*\|' 'EM-016 must remain MISSING unless separately repaired'

# Review note must not approve implementation.
Assert-Pattern $review '^GOVERNANCE REPAIR ACCEPTED — IMPLEMENTATION NOT APPROVED$' 'Review decision must not approve implementation'
Assert-Pattern $review '^Implementation Authority:\s*NONE$' 'Review must preserve Implementation Authority NONE'
Assert-Pattern $review '^Slice Status:\s*BLOCKED$' 'Review must preserve Slice Status BLOCKED'
Assert-Pattern $review '^Source/Test Changes Authorized:\s*NO$' 'Review must reject source/test changes'
Assert-Pattern $review '^Separate Implementation Approval Required:\s*YES$' 'Review must require separate implementation approval'

Assert-NoSourceOrTestChanges

Write-Host "PASS: Slice 1.0 governance repair remains documentation-only."
Write-Host "PASS: Slice Status remains BLOCKED."
Write-Host "PASS: Implementation Authority remains NONE."
Write-Host "PASS: Approval remains NOT APPROVED / BLOCKED."
Write-Host "PASS: Evidence Matrix observed rows keep current statuses."
Write-Host "PASS: Review note does not approve implementation."
Write-Host "PASS: No src/ or tests/ changes detected."
