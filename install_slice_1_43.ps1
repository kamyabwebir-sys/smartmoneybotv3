# install_slice_1_43.ps1
$ErrorActionPreference = "Stop"

$SliceId = "slice_1_43_token_wallet_evidence_artifact_verification_case_matrix_lock"

function Resolve-ProjectRoot {
    $current = (Get-Location).Path

    while ($true) {
        $pyproject = Join-Path $current "pyproject.toml"
        $srcRoot = Join-Path $current "src/smart_money"

        if ((Test-Path $pyproject) -and (Test-Path $srcRoot)) {
            return $current
        }

        $parent = Split-Path -Parent $current
        if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $current) {
            throw "Fail-Closed: Unable to resolve project root from current working directory."
        }

        $current = $parent
    }
}

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )

    $directory = Split-Path -Parent $Path
    if (-not (Test-Path $directory)) {
        New-Item -ItemType Directory -Force -Path $directory | Out-Null
    }

    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path $Path)) {
        throw "Fail-Closed: Missing file for SHA256 calculation: $Path"
    }

    return (Get-FileHash -Algorithm SHA256 -Path $Path).Hash.ToLowerInvariant()
}

function Assert-ProtectedFilesClean {
    param([Parameter(Mandatory = $true)][string[]]$RelativePaths)

    foreach ($relativePath in $RelativePaths) {
        $absolutePath = Join-Path $RepoRoot $relativePath
        if (-not (Test-Path $absolutePath)) {
            throw "Fail-Closed: Protected file missing: $relativePath"
        }
    }

    $gitDirectory = Join-Path $RepoRoot ".git"
    if (Test-Path $gitDirectory) {
        foreach ($relativePath in $RelativePaths) {
            $gitPath = $relativePath -replace "\\", "/"
            $status = git -C $RepoRoot status --porcelain -- $gitPath
            if (-not [string]::IsNullOrWhiteSpace($status)) {
                throw "Fail-Closed: Protected file mutation detected: $relativePath"
            }
        }
    }
}

$RepoRoot = Resolve-ProjectRoot

$FreezePackPath = Join-Path $RepoRoot "docs/freeze_packs/$SliceId.md"
$ReviewPath = Join-Path $RepoRoot "docs/reviews/${SliceId}_review.md"
$VerifierPath = Join-Path $RepoRoot "scripts/verify_${SliceId}.ps1"

$ProtectedFiles = @(
    "src/smart_money/discovery/registry.py",
    "tests/discovery/test_registry.py"
)

Assert-ProtectedFilesClean -RelativePaths $ProtectedFiles

$RegistryHash = Get-Sha256 -Path (Join-Path $RepoRoot "src/smart_money/discovery/registry.py")
$RegistryTestHash = Get-Sha256 -Path (Join-Path $RepoRoot "tests/discovery/test_registry.py")

$FreezePack = @'
# Slice 1.43 - Token and Wallet Evidence Artifact Verification Case Matrix Lock

Status: LOCKED
Scope: Governance / Evidence / Documentation Only
Verifier Mode: Fail-closed
Fast Lane Delivery: ALLOWED
Protected Paths: UNCHANGED REQUIRED

## Current Slice Scope

Slice 1.43 locks the future verification case matrix for token and wallet evidence artifacts.

This slice is governance-only. It does not implement token evidence artifact generation, wallet evidence artifact generation, wallet tracing, token tracing, token scoring, wallet scoring, trading logic, execution logic, risk calculation, opaque ML decisioning, analytics decisioning, reporting behavior, UI behavior, or artifact shape validation.

The verifier for this slice is allowed to verify governance integrity, required tokens, protected file hashes, canonical file placement, and receipt generation only.

## Target Architecture Notes

This slice supports the accepted destination architecture:

- Core
- Domain
- Application
- Adapters
- Analytics
- Reporting

No logic is added to those layers in this slice.

Analytics remains evidence-only and may produce future evidence and score breakdowns only after separate governance approval. It must not make direct trading, execution, risk, or opaque ML decisions.

## Locked Verification Case Matrix

| Case ID | Acceptance Area | Future Verifier Intent | Expected Fail-Closed Behavior | Implementation Now |
|---|---|---|---|---|
| TW-EA-001 | Artifact existence | Verify required token/wallet evidence artifact files exist at canonical paths. | Fail with `MISSING_REQUIRED_ARTIFACT` if any required artifact is absent. | Governance lock only |
| TW-EA-002 | Canonical naming | Verify artifact filenames follow locked canonical naming rules. | Fail with `NON_CANONICAL_ARTIFACT_NAME` if naming drifts. | Governance lock only |
| TW-EA-003 | Canonical hash stability | Verify artifact content hash remains stable across repeated verification. | Fail with `CANONICAL_HASH_DRIFT` if hash changes without governance approval. | Governance lock only |
| TW-EA-004 | Deterministic ordering | Verify wallet/token evidence entries are sorted deterministically. | Fail with `NON_DETERMINISTIC_ORDERING` if filesystem, insertion order, or runtime order affects output. | Governance lock only |
| TW-EA-005 | Shape compliance | Verify artifact shape matches a future locked schema without interpreting evidence meaning. | Fail with `ARTIFACT_SHAPE_VIOLATION` if required fields or structure drift. | Governance lock only |
| TW-EA-006 | Evidence-only boundary | Verify artifact contains evidence metadata only, not trading, risk, decision, or alert output. | Fail with `RUNTIME_LOGIC_LEAKAGE` if execution, risk, score-decision, or alerting logic appears. | Governance lock only |
| TW-EA-007 | Read-only governance boundary | Verify verifier reads artifacts and governance docs only. | Fail with `WRITE_SIDE_EFFECT_DETECTED` if verifier mutates repo state outside receipt generation. | Governance lock only |
| TW-EA-008 | Protected file integrity | Verify protected discovery registry files remain unchanged. | Fail with `PROTECTED_FILE_MUTATION` if protected file hashes drift. | Governance lock only |
| TW-EA-009 | Replayability metadata | Verify future artifact includes deterministic replay metadata such as source id, generated-at policy, and canonical version fields once shape is locked. | Fail with `REPLAY_METADATA_MISSING` if required replay fields are absent. | Governance lock only |
| TW-EA-010 | Scope compliance | Verify no wallet tracing, token scoring, ML inference, trading, risk, or reporting/UI leakage is introduced. | Fail with `SCOPE_GUARDRAIL_VIOLATION` on any forbidden capability. | Governance lock only |

## Fail-Closed Taxonomy

The following fail-closed labels are locked for future verifier use:

- MISSING_REQUIRED_FILE
- MISSING_REQUIRED_TOKEN
- MISSING_REQUIRED_ARTIFACT
- NON_CANONICAL_ARTIFACT_NAME
- CANONICAL_HASH_DRIFT
- NON_DETERMINISTIC_ORDERING
- ARTIFACT_SHAPE_VIOLATION
- RUNTIME_LOGIC_LEAKAGE
- WRITE_SIDE_EFFECT_DETECTED
- PROTECTED_FILE_MUTATION
- REPLAY_METADATA_MISSING
- SCOPE_GUARDRAIL_VIOLATION

## Required Governance Boundaries

No execution/trading logic
No risk calculation
No opaque ML decisioning
No reporting/UI leakage into core/domain logic
No wallet/token tracing implementation
No token/wallet tracing implementation
No token scoring implementation
No wallet scoring implementation
No artifact shape implementation in this slice
No artifact generation implementation in this slice
No runtime behavior implementation in this slice
No changes under `src/`
No changes under `tests/`

## Out-of-Scope Items

This slice does not implement:

- wallet tracing
- token tracing
- token holder graph analysis
- token scoring
- wallet scoring
- trading or execution logic
- risk calculation
- opaque ML inference
- alerting logic
- reporting/UI behavior
- artifact schema validation
- artifact shape validation
- artifact generation
- analytics decisioning
- changes under `src/`
- changes under `tests/`
- changes to protected discovery registry files

## Protected Paths

The following paths must remain unchanged:

- `src/smart_money/discovery/registry.py`
- `tests/discovery/test_registry.py`

## Slice 1.44 Handoff

Slice 1.44 may define Token and Wallet Evidence Artifact Shape Lock after this case matrix is closed.

Slice 1.44 must remain shape/schema governance only unless a later explicit authority grant permits artifact generation or runtime verification.
'@

$Review = @'
# Slice 1.43 Review - Token and Wallet Evidence Artifact Verification Case Matrix Lock

Verdict: PASS-CANDIDATE

Scope: Governance-only

Protected Paths: UNCHANGED REQUIRED

Fast Lane Delivery: ALLOWED

Runtime Logic Leakage: NOT ALLOWED

## Review Summary

Slice 1.43 locks the future verification case matrix for token and wallet evidence artifacts.

It does not implement wallet tracing, token tracing, token scoring, wallet scoring, artifact generation, artifact schema validation, artifact shape validation, execution logic, trading logic, risk calculation, opaque ML decisioning, reporting behavior, UI behavior, analytics decisioning, or runtime behavior.

## Guardrail Review

- Execution Logic: NOT ALLOWED
- Trading Logic: NOT ALLOWED
- Risk Calculation: NOT ALLOWED
- Opaque ML Decisioning: NOT ALLOWED
- Reporting/UI Leakage: NOT ALLOWED
- Runtime Logic Leakage: NOT ALLOWED
- Protected File Mutation: NOT ALLOWED
- Artifact Shape Implementation: NOT ALLOWED IN THIS SLICE
- Artifact Generation Implementation: NOT ALLOWED IN THIS SLICE

## Case Matrix Review

The locked case matrix includes:

- TW-EA-001
- TW-EA-002
- TW-EA-003
- TW-EA-004
- TW-EA-005
- TW-EA-006
- TW-EA-007
- TW-EA-008
- TW-EA-009
- TW-EA-010

## Closure Position

PASS-CANDIDATE is appropriate because this slice is limited to governance documents and a fail-closed verifier for those documents.

No source, test, domain, core, analytics, adapter, reporting, trading, risk, or ML behavior is modified.
'@

$VerifierTemplate = @'
$ErrorActionPreference = "Stop"

$sliceId = "__SLICE_ID__"

$protectedHashesExpected = @{
    "src/smart_money/discovery/registry.py" = "__REGISTRY_HASH__"
    "tests/discovery/test_registry.py" = "__REGISTRY_TEST_HASH__"
}

function Resolve-ProjectRoot {
    $current = (Get-Location).Path

    while ($true) {
        $pyproject = Join-Path $current "pyproject.toml"
        $srcRoot = Join-Path $current "src/smart_money"

        if ((Test-Path $pyproject) -and (Test-Path $srcRoot)) {
            return $current
        }

        $parent = Split-Path -Parent $current
        if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $current) {
            throw "Fail-Closed: Unable to resolve project root from current working directory."
        }

        $current = $parent
    }
}

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path $Path)) {
        throw "Fail-Closed: Missing file for SHA256 calculation: $Path"
    }

    return (Get-FileHash -Algorithm SHA256 -Path $Path).Hash.ToLowerInvariant()
}

function Write-Receipt {
    param(
        [Parameter(Mandatory = $true)][string]$Status,
        [Parameter(Mandatory = $true)][string]$Reason,
        [Parameter(Mandatory = $true)][object]$Details
    )

    $receiptDirectory = Join-Path $repoRoot "artifacts/governance"
    if (-not (Test-Path $receiptDirectory)) {
        New-Item -ItemType Directory -Force -Path $receiptDirectory | Out-Null
    }

    $receiptPath = Join-Path $receiptDirectory "$sliceId.receipt.json"

    $receipt = [ordered]@{
        slice_id = $sliceId
        status = $Status
        reason = $Reason
        verifier_mode = "fail-closed"
        generated_by = "scripts/verify_${sliceId}.ps1"
        details = $Details
    }

    $receipt | ConvertTo-Json -Depth 10 | Set-Content -Path $receiptPath -Encoding utf8NoBOM
}

function Fail {
    param(
        [Parameter(Mandatory = $true)][string]$Reason,
        [Parameter(Mandatory = $true)][object]$Details
    )

    Write-Receipt -Status "FAIL" -Reason $Reason -Details $Details
    throw "Fail-Closed: $Reason"
}

function Require-File {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path $Path)) {
        Fail -Reason "MISSING_REQUIRED_FILE" -Details @{ path = $Path }
    }
}

function Require-Token {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Token,
        [Parameter(Mandatory = $true)][string]$Document
    )

    if (-not $Content.Contains($Token)) {
        Fail -Reason "MISSING_REQUIRED_TOKEN" -Details @{
            document = $Document
            token = $Token
        }
    }
}

$repoRoot = Resolve-ProjectRoot

$freezePackPath = Join-Path $repoRoot "docs/freeze_packs/$sliceId.md"
$reviewPath = Join-Path $repoRoot "docs/reviews/${sliceId}_review.md"
$verifierPath = Join-Path $repoRoot "scripts/verify_${sliceId}.ps1"

Require-File -Path $freezePackPath
Require-File -Path $reviewPath
Require-File -Path $verifierPath

foreach ($relativePath in $protectedHashesExpected.Keys) {
    $absolutePath = Join-Path $repoRoot $relativePath
    Require-File -Path $absolutePath

    $actualHash = Get-Sha256 -Path $absolutePath
    $expectedHash = $protectedHashesExpected[$relativePath]

    if ([string]::IsNullOrWhiteSpace($expectedHash) -or $expectedHash.StartsWith("__")) {
        Fail -Reason "PROTECTED_HASH_PLACEHOLDER" -Details @{
            path = $relativePath
            expected = $expectedHash
        }
    }

    if ($actualHash -ne $expectedHash) {
        Fail -Reason "PROTECTED_FILE_MUTATION" -Details @{
            path = $relativePath
            expected = $expectedHash
            actual = $actualHash
        }
    }
}

$freezePackContent = Get-Content -Raw -Path $freezePackPath
$reviewContent = Get-Content -Raw -Path $reviewPath

$freezePackTokens = @(
    "Slice 1.43 - Token and Wallet Evidence Artifact Verification Case Matrix Lock",
    "Scope: Governance / Evidence / Documentation Only",
    "Verifier Mode: Fail-closed",
    "Fast Lane Delivery: ALLOWED",
    "Protected Paths: UNCHANGED REQUIRED",
    "TW-EA-001",
    "TW-EA-002",
    "TW-EA-003",
    "TW-EA-004",
    "TW-EA-005",
    "TW-EA-006",
    "TW-EA-007",
    "TW-EA-008",
    "TW-EA-009",
    "TW-EA-010",
    "MISSING_REQUIRED_FILE",
    "MISSING_REQUIRED_TOKEN",
    "MISSING_REQUIRED_ARTIFACT",
    "NON_CANONICAL_ARTIFACT_NAME",
    "CANONICAL_HASH_DRIFT",
    "NON_DETERMINISTIC_ORDERING",
    "ARTIFACT_SHAPE_VIOLATION",
    "RUNTIME_LOGIC_LEAKAGE",
    "WRITE_SIDE_EFFECT_DETECTED",
    "PROTECTED_FILE_MUTATION",
    "REPLAY_METADATA_MISSING",
    "SCOPE_GUARDRAIL_VIOLATION",
    "No execution/trading logic",
    "No risk calculation",
    "No opaque ML decisioning",
    "No reporting/UI leakage into core/domain logic",
    "No wallet/token tracing implementation",
    "No token scoring implementation",
    "No artifact shape implementation in this slice",
    "No artifact generation implementation in this slice",
    "No runtime behavior implementation in this slice"
)

foreach ($token in $freezePackTokens) {
    Require-Token -Content $freezePackContent -Token $token -Document "freeze_pack"
}

$reviewTokens = @(
    "Verdict: PASS-CANDIDATE",
    "Scope: Governance-only",
    "Protected Paths: UNCHANGED REQUIRED",
    "Fast Lane Delivery: ALLOWED",
    "Runtime Logic Leakage: NOT ALLOWED",
    "Execution Logic: NOT ALLOWED",
    "Risk Calculation: NOT ALLOWED",
    "Opaque ML Decisioning: NOT ALLOWED",
    "Reporting/UI Leakage: NOT ALLOWED",
    "TW-EA-001",
    "TW-EA-010"
)

foreach ($token in $reviewTokens) {
    Require-Token -Content $reviewContent -Token $token -Document "review"
}

Write-Receipt -Status "PASS" -Reason "SLICE_1_43_VERIFICATION_CASE_MATRIX_LOCK_VERIFIED" -Details @{
    freeze_pack = "docs/freeze_packs/$sliceId.md"
    review = "docs/reviews/${sliceId}_review.md"
    verifier = "scripts/verify_${sliceId}.ps1"
    protected_paths = $protectedHashesExpected.Keys
    case_ids = @(
        "TW-EA-001",
        "TW-EA-002",
        "TW-EA-003",
        "TW-EA-004",
        "TW-EA-005",
        "TW-EA-006",
        "TW-EA-007",
        "TW-EA-008",
        "TW-EA-009",
        "TW-EA-010"
    )
}

Write-Host "PASS: Slice 1.43 verification case matrix lock verified."
'@

$Verifier = $VerifierTemplate `
    -replace "__SLICE_ID__", $SliceId `
    -replace "__REGISTRY_HASH__", $RegistryHash `
    -replace "__REGISTRY_TEST_HASH__", $RegistryTestHash

Write-Utf8NoBom -Path $FreezePackPath -Content $FreezePack
Write-Utf8NoBom -Path $ReviewPath -Content $Review
Write-Utf8NoBom -Path $VerifierPath -Content $Verifier

Write-Host "Installed Slice 1.43 governance package:"
Write-Host " - docs/freeze_packs/$SliceId.md"
Write-Host " - docs/reviews/${SliceId}_review.md"
Write-Host " - scripts/verify_${SliceId}.ps1"

& pwsh -NoProfile -ExecutionPolicy Bypass -File $VerifierPath
