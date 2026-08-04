[CmdletBinding()]
param(
    [switch]$RunVerifier
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
Set-Location $root

$freezeDir = Join-Path $root "docs/freeze_packs"
$reviewDir = Join-Path $root "docs/reviews"
$artifactDir = Join-Path $root "artifacts/governance"
$scriptDir = Join-Path $root "scripts"

$freezePath = Join-Path $freezeDir "slice_1_30_em_003_discovery_registry_consumer_evidence_verification_case_matrix_lock.md"
$reviewPath = Join-Path $reviewDir "slice_1_30_em_003_discovery_registry_consumer_evidence_verification_case_matrix_lock_review.md"
$verifyPath = Join-Path $scriptDir "verify_slice_1_30_em_003_discovery_registry_consumer_evidence_verification_case_matrix_lock.ps1"

foreach ($dir in @($freezeDir, $reviewDir, $artifactDir, $scriptDir)) {
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
    }
}

if (-not (Test-Path -LiteralPath $freezePath)) {
    throw "Missing canonical freeze pack: $freezePath"
}

if (-not (Test-Path -LiteralPath $reviewPath)) {
    throw "Missing canonical review: $reviewPath"
}

if (-not (Test-Path -LiteralPath $verifyPath)) {
    throw "Missing canonical verifier: $verifyPath"
}

Write-Host "Installed Slice 1.30 files."

if ($RunVerifier) {
    & $verifyPath
}
