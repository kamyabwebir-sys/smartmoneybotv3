$ErrorActionPreference = "Stop"

$root = (Get-Location).Path

$required = @(
    "docs/governance/slice_1_40_evidence_matrix_freeze_pack.md",
    "docs/governance/slice_1_40_freeze_pack_governance_index_and_evidence_matrix.md",
    "artifacts/governance/slice_1_40_governance_index_and_evidence_matrix_receipt.json",
    "scripts/install_slice_1_40_governance_index_and_evidence_matrix.ps1",
    "scripts/verify_slice_1_40_governance_index_and_evidence_matrix.ps1"
)

$missing = @()
foreach ($path in $required) {
    $full = Join-Path $root $path
    if (-not (Test-Path $full)) {
        $missing += $path
    }
}

if ($missing.Count -gt 0) {
    Write-Error ("Missing required paths:`n- " + ($missing -join "`n- "))
    exit 1
}

$receiptPath = Join-Path $root "artifacts/governance/slice_1_40_governance_index_and_evidence_matrix_receipt.json"
$receiptText = Get-Content -Path $receiptPath -Raw -Encoding utf8

$requiredTokens = @(
    '"slice": "1.40"',
    '"title": "governance_index_and_evidence_matrix"',
    '"status": "reconstructed"',
    '"mode": "path_based_recovery"',
    '"deterministic": true',
    '"replayable": true'
)

$missingTokens = @()
foreach ($token in $requiredTokens) {
    if (-not $receiptText.Contains($token)) {
        $missingTokens += $token
    }
}

if ($missingTokens.Count -gt 0) {
    Write-Error ("Receipt missing canonical tokens:`n- " + ($missingTokens -join "`n- "))
    exit 1
}

$outputPath = Join-Path $root "artifacts/governance/slice_1_40_governance_index_and_evidence_matrix_verifier_output.md"

$output = @"
# Slice 1.40 Verifier Output

Status: PASS

Validated Paths:
- docs/governance/slice_1_40_evidence_matrix_freeze_pack.md
- docs/governance/slice_1_40_freeze_pack_governance_index_and_evidence_matrix.md
- artifacts/governance/slice_1_40_governance_index_and_evidence_matrix_receipt.json
- scripts/install_slice_1_40_governance_index_and_evidence_matrix.ps1
- scripts/verify_slice_1_40_governance_index_and_evidence_matrix.ps1

Validated Receipt Tokens:
- "slice": "1.40"
- "title": "governance_index_and_evidence_matrix"
- "status": "reconstructed"
- "mode": "path_based_recovery"
- "deterministic": true
- "replayable": true
"@

Set-Content -Path $outputPath -Encoding utf8 -Value $output
Write-Host "Slice 1.40 verification passed."
