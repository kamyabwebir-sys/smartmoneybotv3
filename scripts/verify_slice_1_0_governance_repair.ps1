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
function Assert-Contains {
    param(
        [string]$Path,
        [string]$Text,
        [string]$Description
    )

    $content = Get-Content -LiteralPath $Path -Raw

    if (-not $content.Contains($Text)) {
        throw "Missing text in ${Path}: ${Description}"
    }
}
function Get-NormalizedFileText {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required file not found: ${Path}"
    }

    $resolved = Resolve-Path -LiteralPath $Path
    $bytes = [System.IO.File]::ReadAllBytes($resolved.Path)

    # Prefer strict UTF-8. Fall back to UTF-8 replacement mode if needed.
    try {
        $utf8Strict = New-Object System.Text.UTF8Encoding($false, $true)
        $text = $utf8Strict.GetString($bytes)
    } catch {
        $utf8Loose = New-Object System.Text.UTF8Encoding($false, $false)
        $text = $utf8Loose.GetString($bytes)
    }

    # Normalize common invisible / formatting characters that can break literal matching.
    $text = $text -replace "^\uFEFF", ""
    $text = $text -replace "[\u200B-\u200F\u202A-\u202E\u2060\uFEFF]", ""
    $text = $text -replace "\u00A0", " "

    # Normalize line endings.
    $text = $text -replace "`r`n", "`n"
    $text = $text -replace "`r", "`n"

    return $text
}

function Normalize-AssertionText {
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$Text
    )

    $normalized = if ($null -eq $Text) { "" } else { $Text }

    if ($normalized.Length -gt 0 -and $normalized[0] -eq [char]0xFEFF) {
        $normalized = $normalized.Substring(1)
    }

    $charsToRemove = @(
        [char]0x200B,
        [char]0x200C,
        [char]0x200D,
        [char]0x200E,
        [char]0x200F,
        [char]0x202A,
        [char]0x202B,
        [char]0x202C,
        [char]0x202D,
        [char]0x202E,
        [char]0x2060,
        [char]0xFEFF
    )

    foreach ($ch in $charsToRemove) {
        $normalized = $normalized.Replace([string]$ch, "")
    }

    $normalized = $normalized.Replace([string][char]0x00A0, " ")
    $normalized = $normalized -replace "`r`n", "`n"
    $normalized = $normalized -replace "`r", "`n"
    $normalized = $normalized -replace "\s+", " "

    return $normalized.Trim()
}

function Assert-NormalizedFileLineContains {
    param([Parameter(Mandatory=$true)][string]$Path,
          [Parameter(Mandatory=$true)][string]$Text,
          [Parameter(Mandatory=$true)][string]$Description)
    $fileText = Get-NormalizedFileText -Path $Path
    $needle = Normalize-AssertionText -Text $Text
    foreach ($rawLine in ($fileText -split "`n")) {
        if ((Normalize-AssertionText -Text $rawLine).Contains($needle)) { return }
    }
    throw "Missing normalized line fragment in ${Path}: ${Description}. Expected fragment: ${Text}"
}

function Assert-NormalizedFileContainsFragment {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$Text,

        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    $expected = Normalize-AssertionText $Text
    $lines = Get-Content -LiteralPath $Path -Encoding UTF8

    foreach ($line in $lines) {
        $normalizedLine = Normalize-AssertionText $line
        if ($normalizedLine.Contains($expected)) {
            return
        }
    }

    throw "Missing normalized line fragment in $((Split-Path $Path -Leaf)): $Description. Expected fragment: $expected"
}

function Assert-NormalizedFileLineContains {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Text,

        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    $fileText = Get-NormalizedFileText -Path $Path
    $needle = Normalize-AssertionText -Text $Text

    $rawLines = $fileText -split "`n"

    foreach ($rawLine in $rawLines) {
        $line = Normalize-AssertionText -Text $rawLine

        if ($line.Contains($needle)) {
            return
        }
    }

    throw "Missing normalized line fragment in ${Path}: ${Description}. Expected fragment: ${Text}"
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
function Assert-Contains {
    param(
        [string]$Path,
        [string]$Text,
        [string]$Description
    )

    $content = Get-Content -LiteralPath $Path -Raw

    if (-not $content.Contains($Text)) {
        throw "Missing text in ${Path}: ${Description}"
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
Assert-NormalizedFileLineContains -Path $freeze -Text 'This freeze pack does not approve implementation, source changes, package movement,' -Description 'Freeze Pack non-approval statement must remain present and include implementation disapproval'
Assert-NormalizedFileLineContains -Path $freeze -Text 'Approval Status: BLOCKED' -Description 'Freeze Pack approval status guardrail must remain present'
Assert-NormalizedFileLineContains -Path $freeze -Text 'Status: BLOCKED' -Description 'Freeze Pack status must remain BLOCKED'
Assert-NormalizedFileLineContains -Path $freeze -Text 'Implementation Authority: NONE' -Description 'Freeze Pack implementation authority must remain NONE'
Assert-NormalizedFileLineContains -Path $freeze -Text 'Approval Status: BLOCKED' -Description 'Freeze Pack approval status must remain BLOCKED'

# Current observed Evidence Matrix row statuses.
# This verifier intentionally guards the current file state and does not upgrade EM rows.
Assert-Pattern $matrix '^\|\s*EM-002\s*\|.*\|\s*PARTIAL\s*\|' 'EM-002 must remain PARTIAL unless separately approved'
Assert-Pattern $matrix '^\|\s*EM-003\s*\|.*\|\s*PARTIAL\s*\|' 'EM-003 must be PARTIAL unless separately repaired or completed'
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
Write-Host "PASS: Approval remains BLOCKED."
Write-Host "PASS: Evidence Matrix observed rows keep current statuses."
Write-Host "PASS: Review note does not approve implementation."
Write-Host "PASS: No src/ or tests/ changes detected."
