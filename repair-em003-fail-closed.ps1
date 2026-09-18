# repair-em003-fail-closed.ps1
#
# Purpose:
#   Align EM-003 in the Slice 1.0 Evidence Matrix with the fail-closed
#   verifier expectation.
#
# Scope:
#   Documentation-only governance repair.
#
# Non-Goals:
#   - No src/** changes
#   - No tests/** changes
#   - No package/module moves
#   - No implementation approval
#   - No implementation authority
#
# Expected final governance state:
#   - Slice 1.0 remains BLOCKED
#   - Implementation Authority remains NONE
#   - EM-003 remains MISSING

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$path = 'docs/freeze_packs/slice_1_0_evidence_matrix.md'

$finalLine = '| EM-003 | Repository already has deterministic and replayable design constraints. | | MISSING | Need exact file and line references showing deterministic/replayable requirements. | Blocks contract approval if not fully grounded. |'

$expectedPartialPattern = '^\|\s*EM-003\s*\|\s*Repository already has deterministic and replayable design constraints\.\s*\|.*\|\s*PARTIAL\s*\|\s*Found some evidence for deterministic/replayable, but more specific references needed for full coverage\.\s*\|\s*Blocks contract approval if not fully grounded\.\s*\|$'

$expectedMissingPattern = '^\|\s*EM-003\s*\|\s*Repository already has deterministic and replayable design constraints\.\s*\|.*\|\s*MISSING\s*\|\s*Need exact file and line references showing deterministic/replayable requirements\.\s*\|\s*Blocks contract approval if not fully grounded\.\s*\|$'

if (-not (Test-Path -LiteralPath $path)) {
    throw "Fail-closed: target file not found: $path"
}

$lines = Get-Content -LiteralPath $path

$matchingIndexes = @()

for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\|\s*EM-003\s*\|') {
        $matchingIndexes += $i
    }
}

if ($matchingIndexes.Count -eq 0) {
    throw "Fail-closed: zero EM-003 rows found in $path"
}

if ($matchingIndexes.Count -gt 1) {
    throw "Fail-closed: multiple EM-003 rows found in $path. Count: $($matchingIndexes.Count)"
}

$index = $matchingIndexes[0]
$currentLine = $lines[$index]

if ($currentLine -eq $finalLine) {
    Write-Host 'PASS: EM-003 already matches the final fail-closed verifier-compatible row.'
    Write-Host "File: $path"
    exit 0
}

if ($currentLine -match $expectedPartialPattern) {
    $lines[$index] = $finalLine

    $resolvedPath = (Resolve-Path -LiteralPath $path).Path
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllLines($resolvedPath, $lines, $utf8NoBom)

    Write-Host 'PASS: EM-003 updated from PARTIAL to fail-closed MISSING.'
    Write-Host "File: $path"
    exit 0
}

if ($currentLine -match $expectedMissingPattern) {
    $lines[$index] = $finalLine

    $resolvedPath = (Resolve-Path -LiteralPath $path).Path
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllLines($resolvedPath, $lines, $utf8NoBom)

    Write-Host 'PASS: EM-003 was already semantically MISSING and has been normalized to the exact verifier-compatible row.'
    Write-Host "File: $path"
    exit 0
}

Write-Host 'FAIL-CLOSED: EM-003 row has unexpected shape. Refusing broad rewrite.'
Write-Host ''
Write-Host 'File:'
Write-Host $path
Write-Host ''
Write-Host 'Current row:'
Write-Host $currentLine
Write-Host ''
Write-Host 'Expected final row:'
Write-Host $finalLine

exit 1
