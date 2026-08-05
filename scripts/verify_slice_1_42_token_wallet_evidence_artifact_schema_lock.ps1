Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    $repoRoot = (Get-Location).Path
}
Set-Location $repoRoot

function Fail {
    param(
        [Parameter(Mandatory = $true)][string]$Message
    )
    throw "FAIL-CLOSED: $Message"
}

function Require-File {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        Fail "Required file missing: $Path"
    }
}

function Require-Text {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Text
    )
    $content = Get-Content -LiteralPath $Path -Raw
    if ($content -notmatch [regex]::Escape($Text)) {
        Fail "Required text missing in $Path :: $Text"
    }
}

function Forbid-Text {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Text
    )
    $content = Get-Content -LiteralPath $Path -Raw
    if ($content -match [regex]::Escape($Text)) {
        Fail "Forbidden text detected in $Path :: $Text"
    }
}

function Get-Sha256 {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

$freezePath  = Join-Path $repoRoot "docs/freeze_packs/slice_1_42_token_wallet_evidence_artifact_schema_lock.md"
$matrixPath  = Join-Path $repoRoot "docs/evidence_matrices/slice_1_42_token_wallet_evidence_artifact_schema_lock_matrix.md"
$reviewPath  = Join-Path $repoRoot "docs/reviews/slice_1_42_token_wallet_evidence_artifact_schema_lock_review.md"
$verifyPath  = Join-Path $repoRoot "scripts/verify_slice_1_42_token_wallet_evidence_artifact_schema_lock.ps1"
$receiptPath = Join-Path $repoRoot "artifacts/governance/slice_1_42_token_wallet_evidence_artifact_schema_lock.receipt.json"

$protectedA = Join-Path $repoRoot "src/smart_money/discovery/registry.py"
$protectedB = Join-Path $repoRoot "tests/discovery/test_registry.py"

Require-File $freezePath
Require-File $matrixPath
Require-File $reviewPath
Require-File $verifyPath
Require-File $protectedA
Require-File $protectedB

$freezeRequired = @(
    "Slice ID: 1.42",
    "Governance-only / Contract Lock",
    "Implementation Authority: NO",
    "schema_version: token_wallet_evidence_artifact.v1",
    "artifact_type: evidence_artifact",
    "subject_type: TOKEN | WALLET",
    "subject_id: deterministic string",
    "consumer_version",
    "registry_snapshot_id",
    "registry_entry_id",
    "evidence_refs",
    "deterministic_score_breakdown",
    "replay_manifest_ref",
    "boundary_status",
    "generated_from",
    "BOUNDARY_SAFE",
    "BOUNDARY_BLOCKED",
    "EVIDENCE_INCOMPLETE",
    "REPLAY_REFERENCE_MISSING",
    "Evidence-only",
    "Deterministic",
    "Replayable",
    "Read-only",
    "Boundary-safe",
    "Auditable",
    "Narrow"
)

foreach ($token in $freezeRequired) {
    Require-Text -Path $freezePath -Text $token
}

$reviewRequired = @(
    "Verdict: PASS-CANDIDATE",
    "Scope: Governance-only",
    "Implementation Authority: NO",
    "Protected Paths: UNCHANGED REQUIRED",
    "Execution Logic: NOT ALLOWED",
    "Trading Logic: NOT ALLOWED",
    "Risk Calculation: NOT ALLOWED",
    "Opaque ML Decisioning: NOT ALLOWED",
    "Reporting/UI Leakage: NOT ALLOWED",
    "Registry Mutation: NOT ALLOWED",
    "Direct Promotion Verdict: NOT ALLOWED",
    "Approve as CLOSED / PASS"
)

foreach ($token in $reviewRequired) {
    Require-Text -Path $reviewPath -Text $token
}

$matrixRequired = @(
    "Governance-only",
    "Implementation Authority: NO",
    "Runtime Authority: NO",
    "Schema lock present",
    "Deterministic",
    "Replayable",
    "Read-only",
    "Boundary-safe",
    "Auditable",
    "Forbidden semantics blocked",
    "Protected paths unchanged",
    "Receipt contract present"
)

foreach ($token in $matrixRequired) {
    Require-Text -Path $matrixPath -Text $token
}

$forbiddenDeclared = @(
    "trade execution instruction",
    "order intent",
    "position sizing",
    "stop loss calculation",
    "take profit calculation",
    "risk score used as a decision",
    "opaque ML decision",
    "reporting/UI formatted payload",
    "direct promotion verdict",
    "buy",
    "sell",
    "hold",
    "trade_signal",
    "risk_value",
    "decision"
)

foreach ($token in $forbiddenDeclared) {
    Require-Text -Path $freezePath -Text $token
}

$expectedHashA = "744c4cc809794efb455f209f9857ed0f89a5a97f135e872b0f014f50082742d7"
$expectedHashB = "a68aa20a90826aed09e4bcd61837499583cac5401372a1fbc587de9b636ed26a"

$actualHashA = Get-Sha256 -Path $protectedA
$actualHashB = Get-Sha256 -Path $protectedB

if ($actualHashA -ne $expectedHashA) {
    Fail "Protected path hash mismatch: src/smart_money/discovery/registry.py"
}

if ($actualHashB -ne $expectedHashB) {
    Fail "Protected path hash mismatch: tests/discovery/test_registry.py"
}

$receipt = [ordered]@{
    schema_version = "governance.receipt.v1"
    slice_id = "1.42"
    status = "PASS"
    governance_mode = "FAIL_CLOSED"
    scope = "governance-only"
    locked_contract = "token_wallet_evidence_artifact_schema_lock"
    freeze_pack_path = "docs/freeze_packs/slice_1_42_token_wallet_evidence_artifact_schema_lock.md"
    evidence_matrix_path = "docs/evidence_matrices/slice_1_42_token_wallet_evidence_artifact_schema_lock_matrix.md"
    review_path = "docs/reviews/slice_1_42_token_wallet_evidence_artifact_schema_lock_review.md"
    verifier_path = "scripts/verify_slice_1_42_token_wallet_evidence_artifact_schema_lock.ps1"
    protected_hashes = [ordered]@{
        "src/smart_money/discovery/registry.py" = $actualHashA
        "tests/discovery/test_registry.py" = $actualHashB
    }
}

$receiptDir = Split-Path -Parent $receiptPath
New-Item -ItemType Directory -Force -Path $receiptDir | Out-Null

$json = $receipt | ConvertTo-Json -Depth 6
$json | ConvertFrom-Json | Out-Null

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($receiptPath, $json, $utf8NoBom)

Write-Host "Slice 1.42 verification PASS"
Write-Host "Receipt: $receiptPath"