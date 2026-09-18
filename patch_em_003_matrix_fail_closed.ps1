# patch_em_003_matrix_fail_closed.ps1
# Purpose:
# Align EM-003 evidence matrix state with the fail-closed verifier expectation.
#
# Scope:
# Documentation-only governance repair.
# No src/** changes.
# No tests/** changes.
# No implementation authority.
# Slice 1.0 remains BLOCKED.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$matrixPath = "docs/freeze_packs/slice_1_0_evidence_matrix.md"

$expectedFinalLine = "| EM-003 | Repository already has deterministic and replayable design constraints. | | MISSING | Need exact file and line references showing deterministic/replayable requirements. | Blocks contract approval if not fully grounded. |"

$partialPattern = '^\| EM-003 \| Repository already has deterministic and replayable design constraints\. \|.*\| PARTIAL \| Found some evidence for deterministic/replayable, but more specific references needed for full coverage\. \| Blocks contract approval if not fully grounded\. \|$'

$missingPattern = '^\| EM-003 \| Repository already has deterministic and replayable design constraints\. \|.*\| MISSING \| Need exact file and line references showing deterministic/replayable requirements\. \| Blocks contract approval if not fully grounded\. \|$'

if (-not (Test-Path -LiteralPath $matrixPath)) {
    throw "Evidence matrix not found: $matrixPath"
}

$lines = Get-Content -LiteralPath $matrixPath

$em003Indexes = @()
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\| EM-003 \|') {
        $em003Indexes += $i
    }
}

if ($em003Indexes.Count -eq 0) {
    throw "EM-003 row not found in $matrixPath"
}

if ($em003Indexes.Count -gt 1) {
    throw "Expected exactly one EM-003 row, found $($em003Indexes.Count) in $matrixPath"
}

$idx = $em003Indexes[0]
$currentLine = $lines[$idx]

if ($currentLine -eq $expectedFinalLine) {
    Write-Host "No change needed: EM-003 already matches fail-closed verifier expectation."
    exit 0
}

if ($currentLine -match $partialPattern) {
    $lines[$idx] = $expectedFinalLine

    # Preserve simple deterministic output encoding.
    Set-Content -LiteralPath $matrixPath -Value $lines -Encoding UTF8

    Write-Host "Patched EM-003:"
    Write-Host "  From: PARTIAL"
    Write-Host "  To:   MISSING"
    Write-Host "File: $matrixPath"
    exit 0
}

if ($currentLine -match $missingPattern) {
    # It is semantically already MISSING but not byte-identical to expectedFinalLine.
    # Normalize to exact verifier-compatible line.
    $lines[$idx] = $expectedFinalLine
    Set-Content -LiteralPath $matrixPath -Value $lines -Encoding UTF8

    Write-Host "Normalized EM-003 MISSING row to exact verifier-compatible text."
    Write-Host "File: $matrixPath"
    exit 0
}

throw @"
Unexpected EM-003 row shape. Refusing broad rewrite.

File:
$matrixPath

Current row:
$currentLine

Expected either:
- PARTIAL row with known governance-repair wording
- MISSING row with known verifier wording
"@
