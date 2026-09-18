param(
    [switch]$RunVerifier
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    $repoRoot = (Get-Location).Path
}
Set-Location $repoRoot

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )

    $parent = Split-Path -Parent $Path
    if (-not [string]::IsNullOrWhiteSpace($parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

$sliceId = "1.42"
$sliceName = "slice_1_42_token_wallet_evidence_artifact_schema_lock"

$freezePath  = Join-Path $repoRoot "docs/freeze_packs/$sliceName.md"
$matrixPath  = Join-Path $repoRoot "docs/evidence_matrices/${sliceName}_matrix.md"
$reviewPath  = Join-Path $repoRoot "docs/reviews/${sliceName}_review.md"
$verifyPath  = Join-Path $repoRoot "scripts/verify_${sliceName}.ps1"
$receiptPath = Join-Path $repoRoot "artifacts/governance/${sliceName}.receipt.json"

$freezeContent = @'
# Slice 1.42 — Token and Wallet Evidence Artifact Schema Lock

## Slice Metadata
- Slice ID: 1.42
- Title: Token and Wallet Evidence Artifact Schema Lock
- Type: Governance-only / Contract Lock
- Status Target: CLOSED / PASS
- Implementation Authority: NO
- Runtime Authority: NO
- Registry Mutation Authority: NO

## Objective
Lock the evidence artifact schema for token and wallet subjects as a deterministic, replayable, read-only, evidence-only contract for future consumers.

## Scope
This slice locks schema and governance expectations only.

## Locked Schema
- `schema_version: token_wallet_evidence_artifact.v1`
- `artifact_type: evidence_artifact`
- `subject_type: TOKEN | WALLET`
- `subject_id: deterministic string`
- `chain`
- `consumer_version`
- `registry_snapshot_id`
- `registry_entry_id`
- `evidence_refs`
- `deterministic_score_breakdown` (optional)
- `replay_manifest_ref`
- `boundary_status`
- `generated_from`

## Required Constraints
- Evidence-only
- Deterministic
- Replayable
- Read-only
- Boundary-safe
- Auditable
- Narrow

## Boundary Status Values
- `BOUNDARY_SAFE`
- `BOUNDARY_BLOCKED`
- `EVIDENCE_INCOMPLETE`
- `REPLAY_REFERENCE_MISSING`

## Forbidden Semantics
The locked artifact MUST NOT contain or imply:
- trade execution instruction
- order intent
- position sizing
- stop loss calculation
- take profit calculation
- risk score used as a decision
- opaque ML decision
- reporting/UI formatted payload
- direct promotion verdict
- buy
- sell
- hold
- trade_signal
- risk_value
- decision

## Protected Paths
The following protected paths MUST remain unchanged from the locked reference hashes:
- `src/smart_money/discovery/registry.py`
- `tests/discovery/test_registry.py`

## Reference Protected Hashes
- `src/smart_money/discovery/registry.py` -> `744c4cc809794efb455f209f9857ed0f89a5a97f135e872b0f014f50082742d7`
- `tests/discovery/test_registry.py` -> `a68aa20a90826aed09e4bcd61837499583cac5401372a1fbc587de9b636ed26a`

## Out of Scope
- generator
- token scanner
- wallet scanner
- Solana adapter
- Base adapter
- Robinhood adapter
- registry mutation
- discovery runtime
- execution logic
- trading logic
- risk calculation
- promotion logic
- reporting/UI payload shaping
- opaque ML

## Acceptance Criteria
- Freeze pack exists
- Evidence matrix exists
- Review exists
- Verifier exists
- Required schema tokens are present in governance docs
- Forbidden semantics are explicitly blocked
- Protected path hashes match locked references
- Receipt is emitted as valid JSON
- Verifier fails closed on any mismatch
'@

$matrixContent = @'
# Slice 1.42 — Token and Wallet Evidence Artifact Schema Lock Matrix

| Requirement | Expected Evidence | Status Rule |
| --- | --- | --- |
| Governance-only | Freeze pack and review explicitly state governance-only | REQUIRED |
| Implementation Authority: NO | Review explicitly denies implementation authority | REQUIRED |
| Runtime Authority: NO | Freeze pack explicitly denies runtime authority | REQUIRED |
| Schema lock present | Freeze pack locks token/wallet evidence artifact schema | REQUIRED |
| Deterministic | Freeze pack states deterministic | REQUIRED |
| Replayable | Freeze pack states replayable | REQUIRED |
| Read-only | Freeze pack states read-only | REQUIRED |
| Boundary-safe | Freeze pack defines allowed boundary statuses | REQUIRED |
| Auditable | Freeze pack states auditable | REQUIRED |
| Forbidden semantics blocked | Freeze pack explicitly lists forbidden semantics | REQUIRED |
| Protected paths unchanged | Verifier compares protected hashes | REQUIRED |
| Receipt contract present | Verifier writes governance receipt JSON | REQUIRED |
'@

$reviewContent = @'
# Slice 1.42 — Token and Wallet Evidence Artifact Schema Lock Review

Verdict: PASS-CANDIDATE
Scope: Governance-only
Implementation Authority: NO
Protected Paths: UNCHANGED REQUIRED
Execution Logic: NOT ALLOWED
Trading Logic: NOT ALLOWED
Risk Calculation: NOT ALLOWED
Opaque ML Decisioning: NOT ALLOWED
Reporting/UI Leakage: NOT ALLOWED
Registry Mutation: NOT ALLOWED
Direct Promotion Verdict: NOT ALLOWED

## Review Summary
This slice is a governance-only schema lock for token and wallet evidence artifacts.
It does not authorize generator implementation, runtime discovery behavior, execution logic, or registry mutation.

Approve as CLOSED / PASS
'@

$verifyContent = @'
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
'@

Write-Utf8NoBom -Path $freezePath -Content $freezeContent
Write-Utf8NoBom -Path $matrixPath -Content $matrixContent
Write-Utf8NoBom -Path $reviewPath -Content $reviewContent
Write-Utf8NoBom -Path $verifyPath -Content $verifyContent

Write-Host "Slice 1.42 scaffolding complete."
Write-Host "Freeze Pack : $freezePath"
Write-Host "Matrix      : $matrixPath"
Write-Host "Review      : $reviewPath"
Write-Host "Verifier    : $verifyPath"

if ($RunVerifier) {
    & $verifyPath
}
