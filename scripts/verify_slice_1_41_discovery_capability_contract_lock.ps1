Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail {
    param([string]$Message)
    Write-Error "Slice 1.41 verifier FAIL: $Message"
    exit 1
}

function Require-File {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Fail "Required file missing: $Path"
    }
}

function Require-Directory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        Fail "Required directory missing: $Path"
    }
}

function Require-Token {
    param(
        [string]$Path,
        [string[]]$Tokens
    )

    Require-File $Path
    $content = Get-Content -LiteralPath $Path -Raw -Encoding UTF8

    foreach ($token in $Tokens) {
        if ($content -notlike "*$token*") {
            Fail "Required token missing from $Path :: $token"
        }
    }
}

function Get-Sha256 {
    param([string]$Path)

    Require-File $Path
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($ScriptRoot)) {
    $ScriptRoot = (Get-Location).Path
}

$RepoRoot = Split-Path -Parent $ScriptRoot
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Get-Location).Path
}

Set-Location $RepoRoot

$SliceId = "slice_1_41_discovery_capability_contract_lock"

$FreezePath = Join-Path $RepoRoot "docs/freeze_packs/$SliceId.md"
$MatrixPath = Join-Path $RepoRoot "docs/evidence_matrices/$SliceId`_matrix.md"
$ReviewPath = Join-Path $RepoRoot "docs/reviews/$SliceId`_review.md"
$VerifierPath = Join-Path $RepoRoot "scripts/verify_$SliceId.ps1"
$ArtifactsDir = Join-Path $RepoRoot "artifacts/governance"
$ReceiptPath = Join-Path $ArtifactsDir "$SliceId.receipt.json"

$ProtectedRegistryPath = "src/smart_money/discovery/registry.py"
$ProtectedRegistryTestPath = "tests/discovery/test_registry.py"

$ExpectedRegistrySha256 = "744c4cc809794efb455f209f9857ed0f89a5a97f135e872b0f014f50082742d7"
$ExpectedRegistryTestSha256 = "a68aa20a90826aed09e4bcd61837499583cac5401372a1fbc587de9b636ed26a"

Require-Directory (Join-Path $RepoRoot "docs")
Require-Directory (Join-Path $RepoRoot "docs/freeze_packs")
Require-Directory (Join-Path $RepoRoot "docs/evidence_matrices")
Require-Directory (Join-Path $RepoRoot "docs/reviews")
Require-Directory (Join-Path $RepoRoot "scripts")

Require-File $FreezePath
Require-File $MatrixPath
Require-File $ReviewPath
Require-File $VerifierPath
Require-File (Join-Path $RepoRoot $ProtectedRegistryPath)
Require-File (Join-Path $RepoRoot $ProtectedRegistryTestPath)

$freezeTokens = @(
    "Slice Type: Governance-only",
    "Contract Status: CONTRACT_LOCKED",
    "Promotion Gate: LOCKED",
    "Implementation Authority: NO",
    "Verifier Mode: Fail-closed",
    "output is deterministic",
    "output is replayable",
    "execution/trading logic: NOT ALLOWED",
    "risk calculation: NOT ALLOWED",
    "opaque ML decisioning: NOT ALLOWED",
    "reporting/UI leakage: NOT ALLOWED",
    "live discovery execution: NOT ALLOWED",
    "registry mutation: NOT ALLOWED",
    "token evidence artifact",
    "wallet evidence artifact",
    "canonical serialization required",
    "stable schema version required",
    "Analytics may produce evidence and score breakdown",
    "Analytics must not produce direct operational decisions",
    "Review Verdict: PASS-CANDIDATE",
    "Approve as CLOSED / PASS"
)

$matrixTokens = @(
    "Slice Type: Governance-only",
    "Contract Status: CONTRACT_LOCKED",
    "Promotion Gate: LOCKED",
    "Implementation Authority: NO",
    "Verifier Mode: Fail-closed",
    "Protected registry hash unchanged",
    "Protected registry test hash unchanged",
    "No execution/trading logic",
    "No risk calculation",
    "No opaque ML decisioning",
    "No reporting/UI leakage",
    "Deterministic output",
    "Replayable output",
    "token evidence artifact",
    "wallet evidence artifact",
    "Analytics may produce evidence and score breakdown",
    "Analytics must not produce direct operational decisions",
    "Review Verdict: PASS-CANDIDATE"
)

$reviewTokens = @(
    "Slice Type: Governance-only",
    "Contract Status: CONTRACT_LOCKED",
    "Promotion Gate: LOCKED",
    "Implementation Authority: NO",
    "Verifier Mode: Fail-closed",
    "Review Verdict: PASS-CANDIDATE",
    "Approve as CLOSED / PASS",
    "runtime discovery implementation",
    "trading or execution behavior",
    "risk calculation",
    "opaque ML decisioning",
    "reporting/UI behavior inside core/domain",
    "The closure receipt must be deterministic and replayable",
    "Analytics may produce evidence and score breakdown",
    "Analytics must not produce direct operational decisions"
)

Require-Token $FreezePath $freezeTokens
Require-Token $MatrixPath $matrixTokens
Require-Token $ReviewPath $reviewTokens

$actualRegistrySha256 = Get-Sha256 (Join-Path $RepoRoot $ProtectedRegistryPath)
$actualRegistryTestSha256 = Get-Sha256 (Join-Path $RepoRoot $ProtectedRegistryTestPath)

if ($actualRegistrySha256 -ne $ExpectedRegistrySha256) {
    Fail "Protected registry hash mismatch. Expected $ExpectedRegistrySha256 but got $actualRegistrySha256"
}

if ($actualRegistryTestSha256 -ne $ExpectedRegistryTestSha256) {
    Fail "Protected registry test hash mismatch. Expected $ExpectedRegistryTestSha256 but got $actualRegistryTestSha256"
}

if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot ".git") -PathType Container)) {
    Fail "Git metadata is required to verify protected paths fail-closed."
}

$protectedPaths = @(
    $ProtectedRegistryPath,
    $ProtectedRegistryTestPath
)

$gitStatus = git status --porcelain -- $protectedPaths 2>$null
if ($LASTEXITCODE -ne 0) {
    Fail "Unable to inspect protected path git status."
}

if (-not [string]::IsNullOrWhiteSpace(($gitStatus | Out-String))) {
    Fail "Protected registry paths are modified or untracked."
}

New-Item -ItemType Directory -Force -Path $ArtifactsDir | Out-Null

$freezeSha256 = Get-Sha256 $FreezePath
$matrixSha256 = Get-Sha256 $MatrixPath
$reviewSha256 = Get-Sha256 $ReviewPath
$verifierSha256 = Get-Sha256 $VerifierPath

$receipt = [ordered]@{
    slice_id = $SliceId
    slice_type = "Governance-only"
    contract_status = "CONTRACT_LOCKED"
    promotion_gate = "LOCKED"
    verifier_mode = "Fail-closed"
    implementation_authority = "NO"
    deterministic = $true
    replayable = $true
    guardrails = [ordered]@{
        no_execution_logic = $true
        no_trading_logic = $true
        no_risk_calculation = $true
        no_opaque_ml_decisioning = $true
        no_reporting_ui_leakage = $true
        registry_mutation_allowed = $false
    }
    protected_files = [ordered]@{
        registry_py = [ordered]@{
            path = $ProtectedRegistryPath
            sha256 = $actualRegistrySha256
        }
        test_registry_py = [ordered]@{
            path = $ProtectedRegistryTestPath
            sha256 = $actualRegistryTestSha256
        }
    }
    governance_artifacts = [ordered]@{
        freeze_pack = [ordered]@{
            path = "docs/freeze_packs/$SliceId.md"
            sha256 = $freezeSha256
        }
        evidence_matrix = [ordered]@{
            path = "docs/evidence_matrices/$SliceId`_matrix.md"
            sha256 = $matrixSha256
        }
        review = [ordered]@{
            path = "docs/reviews/$SliceId`_review.md"
            sha256 = $reviewSha256
        }
        verifier = [ordered]@{
            path = "scripts/verify_$SliceId.ps1"
            sha256 = $verifierSha256
        }
    }
    verdict = "PASS"
}

$json = $receipt | ConvertTo-Json -Depth 20
Set-Content -LiteralPath $ReceiptPath -Value $json -Encoding utf8NoBOM

Write-Host "Slice 1.41 verifier PASS: $ReceiptPath"
