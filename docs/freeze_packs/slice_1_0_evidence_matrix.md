$ErrorActionPreference = "Stop"

$path = "docs/freeze_packs/slice_1_0_evidence_matrix.md"

if (-not (Test-Path $path)) {
    throw "File not found: $path"
}

$content = Get-Content -Path $path -Raw

$oldPattern = '(?m)^\|?\s*EM-003\s*\|.*$'

$matches = [regex]::Matches($content, $oldPattern)

if ($matches.Count -ne 1) {
    throw "Expected exactly one EM-003 row, found $($matches.Count). Refusing to modify."
}

$newRow = "| EM-003 | Deterministic and replayable design constraints are fully grounded. | MISSING | Need exact file and line references showing deterministic/replayable requirements. | Blocks contract approval if not fully grounded. |"

$newContent = [regex]::Replace($content, $oldPattern, $newRow)

if ($newContent -eq $content) {
    throw "No content change detected. Refusing silent success."
}

Set-Content -Path $path -Value $newContent -NoNewline -Encoding UTF8

Write-Host "Updated EM-003 row to verifier-aligned MISSING state."
