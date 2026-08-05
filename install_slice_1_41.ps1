param(
    [switch]$RunVerifier
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($ScriptRoot)) {
    $ScriptRoot = (Get-Location).Path
}

$RepoRoot = $ScriptRoot
Set-Location $RepoRoot

$SliceId = "slice_1_41_discovery_capability_contract_lock"

$FreezeDir = Join-Path $RepoRoot "docs/freeze_packs"
$MatrixDir = Join-Path $RepoRoot "docs/evidence_matrices"
$ReviewDir = Join-Path $RepoRoot "docs/reviews"
$ScriptsDir = Join-Path $RepoRoot "scripts"
$ArtifactsDir = Join-Path $RepoRoot "artifacts/governance"

$FreezePath = Join-Path $FreezeDir "$SliceId.md"
$MatrixPath = Join-Path $MatrixDir "$SliceId`_matrix.md"
$ReviewPath = Join-Path $ReviewDir "$SliceId`_review.md"
$VerifierPath = Join-Path $ScriptsDir "verify_$SliceId.ps1"

New-Item -ItemType Directory -Force -Path $FreezeDir | Out-Null
New-Item -ItemType Directory -Force -Path $MatrixDir | Out-Null
New-Item -ItemType Directory -Force -Path $ReviewDir | Out-Null
New-Item -ItemType Directory -Force -Path $ScriptsDir | Out-Null
New-Item -ItemType Directory -Force -Path $ArtifactsDir | Out-Null

$FreezePack = @'
# Slice 1.41 - Discovery Capability Contract Lock: Token and Wallet Evidence Artifacts

## Slice Identity

- Slice ID: slice_1_41_discovery_capability_contract_lock
- Slice Type: Governance-only
- Contract Status: CONTRACT_LOCKED
- Promotion Gate: LOCKED
- Implementation Authority: NO
- Verifier Mode: Fail-closed
- output is deterministic
- output is replayable

## Purpose

This slice locks the governance contract for future discovery capability evidence artifacts.

This slice defines the permitted shape and constraints for token evidence artifacts and wallet evidence artifacts.

This slice is a contract lock only.

## Explicit Non-Goals

The following are NOT ALLOWED in this slice:

- execution/trading logic: NOT ALLOWED
- risk calculation: NOT ALLOWED
- opaque ML decisioning: NOT ALLOWED
- reporting/UI leakage: NOT ALLOWED
- live discovery execution: NOT ALLOWED
- registry mutation: NOT ALLOWED
- exchange/broker integration: NOT ALLOWED
- Solana/Base/Robinhood network access: NOT ALLOWED
- wallet scoring decision: NOT ALLOWED
- token buy/sell/hold decision: NOT ALLOWED

## Protected Baseline

The following protected files must not be modified by this slice:

- src/smart_money/discovery/registry.py
- tests/discovery/test_registry.py

Expected SHA256 values:

- src/smart_money/discovery/registry.py: 744c4cc809794efb455f209f9857ed0f89a5a97f135e872b0f014f50082742d7
- tests/discovery/test_registry.py: a68aa20a90826aed09e4bcd61837499583cac5401372a1fbc587de9b636ed26a

The verifier must fail closed if either protected file is missing, modified, untracked, or has a hash mismatch.

## Locked Capability Contract

Future discovery evidence artifacts may describe observed evidence only.

Allowed artifact categories:

- token evidence artifact
- wallet evidence artifact

Allowed artifact behavior:

- preserve deterministic identity
- preserve canonical serialization
- preserve replayable evidence fields
- expose evidence source labels
- expose score breakdown only when score components are deterministic and explainable
- provide stable reason codes
- provide stable schema version

Disallowed artifact behavior:

- direct execution decisions
- direct trading decisions
- direct risk decisions
- opaque model decisions
- mutation of discovery registry
- mutation of protected baseline files
- reporting/UI formatting inside core/domain logic

## Token Evidence Artifact Contract

A future token evidence artifact may include deterministic evidence such as:

- token identifier
- chain identifier
- observation window identifier
- deterministic artifact id
- schema version
- evidence source labels
- observed liquidity evidence
- observed holder distribution evidence
- observed activity evidence
- observed market-structure evidence
- deterministic score component breakdown
- stable reason codes

A token evidence artifact must not decide whether to buy, sell, hold, trade, execute, block, approve, or size a position.

## Wallet Evidence Artifact Contract

A future wallet evidence artifact may include deterministic evidence such as:

- wallet identifier
- chain identifier
- observation window identifier
- deterministic artifact id
- schema version
- evidence source labels
- observed token interaction evidence
- observed timing evidence
- observed clustering evidence
- observed activity evidence
- deterministic score component breakdown
- stable reason codes

A wallet evidence artifact must not decide whether a wallet is safe, unsafe, tradable, blocked, approved, or execution-worthy.

## Determinism Requirements

All future evidence artifact implementations under this contract must be deterministic.

Required deterministic properties:

- no wall-clock dependency in artifact identity
- no random identifiers
- no unordered map serialization leakage
- no environment-dependent output
- no hidden network dependency
- no non-replayable source dependency
- canonical serialization required
- stable schema version required

## Replayability Requirements

All future evidence artifact implementations under this contract must be replayable.

Required replayability properties:

- input references must be explicit
- observation window must be explicit
- evidence source labels must be explicit
- score component breakdown must be inspectable
- reason codes must be stable
- artifact identity must be reproducible from canonical inputs

## Analytics Boundary

Analytics may produce evidence and score breakdown.

Analytics must not produce direct operational decisions.

Allowed:

- evidence extraction
- deterministic score components
- explainable score breakdown
- stable reason codes

Not allowed:

- trade decision
- execution instruction
- position sizing
- risk calculation
- opaque ML decisioning

## Architecture Boundary

This slice aligns with the target architecture:

- Core / Domain / Application / Adapters / Analytics / Reporting

This slice does not require a broad refactor.

This slice does not move files between architecture layers.

This slice does not introduce runtime behavior.

## Acceptance Criteria

This slice is accepted only if:

- freeze pack exists
- evidence matrix exists
- review exists
- verifier exists
- verifier runs fail-closed
- protected registry file hash is unchanged
- protected registry test file hash is unchanged
- governance documents contain required contract tokens
- no execution/trading logic is introduced
- no risk calculation is introduced
- no opaque ML decisioning is introduced
- no reporting/UI leakage is introduced
- output is deterministic
- output is replayable

## Closure

Review Verdict: PASS-CANDIDATE

Approve as CLOSED / PASS only after the verifier succeeds.

Implementation Authority: NO
'@

$EvidenceMatrix = @'
# Slice 1.41 Evidence Matrix - Discovery Capability Contract Lock

## Matrix Identity

- Slice ID: slice_1_41_discovery_capability_contract_lock
- Slice Type: Governance-only
- Contract Status: CONTRACT_LOCKED
- Promotion Gate: LOCKED
- Verifier Mode: Fail-closed
- Implementation Authority: NO

## Evidence Rows

| Evidence ID | Claim | Required Evidence | Status |
|---|---|---|---|
| EM-001 | Freeze pack exists | docs/freeze_packs/slice_1_41_discovery_capability_contract_lock.md | LOCKED |
| EM-002 | Evidence matrix exists | docs/evidence_matrices/slice_1_41_discovery_capability_contract_lock_matrix.md | LOCKED |
| EM-003 | Review exists | docs/reviews/slice_1_41_discovery_capability_contract_lock_review.md | LOCKED |
| EM-004 | Verifier exists | scripts/verify_slice_1_41_discovery_capability_contract_lock.ps1 | LOCKED |
| EM-005 | Protected registry hash unchanged | src/smart_money/discovery/registry.py SHA256 check | LOCKED |
| EM-006 | Protected registry test hash unchanged | tests/discovery/test_registry.py SHA256 check | LOCKED |
| EM-007 | No execution/trading logic | Required governance token check | LOCKED |
| EM-008 | No risk calculation | Required governance token check | LOCKED |
| EM-009 | No opaque ML decisioning | Required governance token check | LOCKED |
| EM-010 | No reporting/UI leakage | Required governance token check | LOCKED |
| EM-011 | Deterministic output | Required governance token check | LOCKED |
| EM-012 | Replayable output | Required governance token check | LOCKED |
| EM-013 | Discovery capability artifact contract locked | Token and wallet evidence artifact contract text | LOCKED |
| EM-014 | Analytics boundary preserved | Analytics may produce evidence and score breakdown only | LOCKED |
| EM-015 | Implementation authority denied | Implementation Authority: NO | LOCKED |

## Guardrail Matrix

| Guardrail | Required State | Slice 1.41 State |
|---|---|---|
| No execution logic | REQUIRED | SATISFIED |
| No trading logic | REQUIRED | SATISFIED |
| No risk calculation | REQUIRED | SATISFIED |
| No opaque ML decisioning | REQUIRED | SATISFIED |
| No reporting/UI leakage | REQUIRED | SATISFIED |
| No registry mutation | REQUIRED | SATISFIED |
| Deterministic | REQUIRED | SATISFIED |
| Replayable | REQUIRED | SATISFIED |
| Fail-closed verification | REQUIRED | SATISFIED |

## Required Verifier Tokens

The verifier must require the following tokens:

- Slice Type: Governance-only
- Contract Status: CONTRACT_LOCKED
- Promotion Gate: LOCKED
- Implementation Authority: NO
- Verifier Mode: Fail-closed
- output is deterministic
- output is replayable
- execution/trading logic: NOT ALLOWED
- risk calculation: NOT ALLOWED
- opaque ML decisioning: NOT ALLOWED
- reporting/UI leakage: NOT ALLOWED
- token evidence artifact
- wallet evidence artifact
- Analytics may produce evidence and score breakdown
- Analytics must not produce direct operational decisions

## Closure

Review Verdict: PASS-CANDIDATE

Approve as CLOSED / PASS only after verifier success.
'@

$Review = @'
# Slice 1.41 Review - Discovery Capability Contract Lock

## Review Identity

- Slice ID: slice_1_41_discovery_capability_contract_lock
- Slice Type: Governance-only
- Contract Status: CONTRACT_LOCKED
- Promotion Gate: LOCKED
- Verifier Mode: Fail-closed
- Implementation Authority: NO

## Review Summary

This review confirms that Slice 1.41 is a governance-only contract lock for future token and wallet evidence artifacts.

The slice does not implement discovery execution.

The slice does not modify the protected discovery registry baseline.

The slice does not introduce trading, execution, risk, opaque ML, reporting, or UI behavior.

## Boundary Review

Accepted:

- contract wording for token evidence artifact
- contract wording for wallet evidence artifact
- deterministic requirements
- replayable requirements
- analytics boundary requirements
- fail-closed verifier requirement
- protected-file guard requirement

Rejected / Not Authorized:

- runtime discovery implementation
- trading or execution behavior
- risk calculation
- opaque ML decisioning
- reporting/UI behavior inside core/domain
- mutation of src/smart_money/discovery/registry.py
- mutation of tests/discovery/test_registry.py

## Protected Path Review

Protected paths:

- src/smart_money/discovery/registry.py
- tests/discovery/test_registry.py

Required state:

- files must exist
- files must match expected SHA256
- files must not be modified
- files must not be untracked
- verifier must fail closed if Git metadata is unavailable

## Determinism Review

The slice is deterministic because it only writes static governance documents and a deterministic verifier.

The closure receipt must be deterministic and replayable.

No timestamp is required for closure.

No random value is allowed for closure.

## Replayability Review

The slice is replayable because verifier output is derived from:

- static governance document contents
- protected file SHA256 values
- deterministic document hashes
- fixed slice identity

## Analytics Boundary Review

Analytics may produce evidence and score breakdown.

Analytics must not produce direct operational decisions.

This preserves the project guardrail that analytics outputs evidence and explainable score components, not trading decisions.

## Final Verdict

Review Verdict: PASS-CANDIDATE

Approve as CLOSED / PASS after successful verifier execution.

Implementation Authority: NO
'@

$Verifier = @'
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
'@

Set-Content -LiteralPath $FreezePath -Value $FreezePack -Encoding utf8NoBOM
Set-Content -LiteralPath $MatrixPath -Value $EvidenceMatrix -Encoding utf8NoBOM
Set-Content -LiteralPath $ReviewPath -Value $Review -Encoding utf8NoBOM
Set-Content -LiteralPath $VerifierPath -Value $Verifier -Encoding utf8NoBOM

Write-Host "Slice 1.41 installer wrote:"
Write-Host " - $FreezePath"
Write-Host " - $MatrixPath"
Write-Host " - $ReviewPath"
Write-Host " - $VerifierPath"

if ($RunVerifier) {
    Write-Host "Running embedded verifier..."
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $VerifierPath
    if ($LASTEXITCODE -ne 0) {
        throw "Slice 1.41 verifier failed."
    }
}
else {
    Write-Host "Verifier not run. To run:"
    Write-Host "pwsh -NoProfile -ExecutionPolicy Bypass -File `"$VerifierPath`""
}
