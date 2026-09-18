$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$receiptPath = Join-Path $root "artifacts/governance/slice_b7_29_phase_closure.receipt.json"
$receipt = Get-Content -Raw -LiteralPath $receiptPath | ConvertFrom-Json

if ($receipt.status -ne "PASS") {
    throw "B7.29 receipt status is not PASS"
}
if ($receipt.tests.full_suite.passed -ne 568 -or $receipt.tests.full_suite.failed -ne 0) {
    throw "B7.29 full-suite counts do not match the frozen receipt"
}
if ($receipt.release_baseline_id -ne "phase_b7_release_baseline_86ad16c29ef2d04d05a9b083415ecb07") {
    throw "B7.29 release identity mismatch"
}

Push-Location $root
try {
    & pwsh -NoProfile -File ".\verify_contract_integrity.ps1"
    if ($LASTEXITCODE -ne 0) { throw "contract verifier failed" }
    & python ".agents/skills/boundary-enforcer/scripts/check_boundaries.py"
    if ($LASTEXITCODE -ne 0) { throw "boundary verifier failed" }
    & git diff --exit-code c1432d0 -- `
        "src/smart_money/discovery/registry.py" `
        "tests/discovery/test_registry.py"
    if ($LASTEXITCODE -ne 0) { throw "protected Discovery baseline changed" }
}
finally {
    Pop-Location
}

Write-Output "slice-b7.29-phase-closure: PASS"
