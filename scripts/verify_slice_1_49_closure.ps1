# verify_slice_1_49_closure.ps1
# Deterministic Governance Verifier for Slice 1.49 Ingestion Scope
# Run environment: PowerShell 7.6.4+ (Dev) / Linux (Prod)

$ErrorActionPreference = "Stop"

# PWD Fallback mechanism
$TargetDir = $PWD
if ($TargetDir.Path -like "*scripts*") {
    $TargetDir = Resolve-Path "$TargetDir\.."
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Verifying Slice 1.49 Governance & Integrity..." -ForegroundColor Cyan
Write-Host "Working Directory: $TargetDir" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Required Files Presence
$RequiredFiles = @(
    "docs/freeze_packs/slice_1_49_governance_freeze_pack.md",
    "docs/freeze_packs/slice_1_49_post_1_48_next_scope_grounding.md"
)

foreach ($File in $RequiredFiles) {
    $Path = Join-Path $TargetDir $File
    if (-not (Test-Path $Path)) {
        Write-Error "CRITICAL: Required governance file missing: $File"
    } else {
        Write-Host "PASS: Found $File" -ForegroundColor Green
    }
}

# 2. Strict Content Audit on Freeze Pack
$FreezePackPath = Join-Path $TargetDir "docs/freeze_packs/slice_1_49_governance_freeze_pack.md"
$Content = Get-Content $FreezePackPath -Raw

if ($Content -notlike "*FAIL_CLOSED*") {
    Write-Error "CRITICAL: Slice 1.49 Freeze Pack is not in FAIL_CLOSED mode."
} else {
    Write-Host "PASS: Freeze Pack enforcement mode is FAIL_CLOSED" -ForegroundColor Green
}

if ($Content -notlike "*READ_ONLY*") {
    Write-Error "CRITICAL: Slice 1.49 Freeze Pack status is not READ_ONLY."
} else {
    Write-Host "PASS: Freeze Pack status is READ_ONLY" -ForegroundColor Green
}

# 3. Guardrail Enforcement: Ensure NO active execution or risk code has leaked
$DiscoveryDir = Join-Path $TargetDir "src/smart_money/discovery"
if (Test-Path $DiscoveryDir) {
    $ForbiddenDefinitions = @(
        "(?m)^\s*(async\s+)?def\s+execute_order\b",
        "(?m)^\s*(async\s+)?def\s+calculate_risk\b",
        "(?m)^\s*class\s+OpaqueMlDecision"
    )

    foreach ($SourceFile in Get-ChildItem -Path $DiscoveryDir -Filter "*.py" -Recurse) {
        $SourceText = Get-Content -LiteralPath $SourceFile.FullName -Raw
        foreach ($Pattern in $ForbiddenDefinitions) {
            if ($SourceText -match $Pattern) {
                Write-Error "CRITICAL: Guardrail breach in $($SourceFile.FullName): $Pattern"
            }
        }
    }

    Write-Host "PASS: Guardrails verified. No execution or risk implementation leaked." -ForegroundColor Green
}

Write-Host "----------------------------------------------------------" -ForegroundColor Cyan
Write-Host "VERDICT: Slice 1.49 Closure Verified Successfully." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
