$ErrorActionPreference = "Stop"

$sliceId = "slice_1_43_token_wallet_evidence_artifact_verification_case_matrix_lock"

$protectedHashesExpected = @{
    "src/smart_money/discovery/registry.py" = "744c4cc809794efb455f209f9857ed0f89a5a97f135e872b0f014f50082742d7"
    "tests/discovery/test_registry.py" = "a68aa20a90826aed09e4bcd61837499583cac5401372a1fbc587de9b636ed26a"
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