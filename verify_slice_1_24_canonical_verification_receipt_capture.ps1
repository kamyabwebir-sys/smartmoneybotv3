# verify_slice_1_24_canonical_verification_receipt_capture.ps1
# Deterministic verifier for Slice 1.24 receipt capture.
# Governance-only. No product logic. No EM-003 promotion.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail {
    param([string]$Message)
    throw "[slice-1.24 verifier] $Message"
}

function Require-Path {
    param([string]$PathValue)
    if (-not (Test-Path $PathValue)) {
        Fail "Required path missing: $PathValue"
    }
}

function ConvertTo-CanonicalJson {
    param([Parameter(Mandatory = $true)] $Value)
    return ($Value | ConvertTo-Json -Depth 30 -Compress)
}

function Get-Sha256Hex {
    param([Parameter(Mandatory = $true)][string]$Text)

    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
        $hashBytes = $sha.ComputeHash($bytes)
        return (($hashBytes | ForEach-Object { $_.ToString("x2") }) -join "")
    }
    finally {
        $sha.Dispose()
    }
}

function Assert-RelativePath {
    param([string]$PathValue)

    if ([string]::IsNullOrWhiteSpace($PathValue)) {
        Fail "Path value is empty."
    }

    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        Fail "Absolute path is forbidden in receipt: $PathValue"
    }

    if ($PathValue -match "^[A-Za-z]:\\") {
        Fail "Windows absolute path is forbidden in receipt: $PathValue"
    }

    if ($PathValue -match "\\") {
        Fail "Backslash path separator is forbidden in canonical receipt path: $PathValue"
    }

    if ($PathValue -match "\.\.") {
        Fail "Parent traversal is forbidden in receipt path: $PathValue"
    }
}

function Assert-NoTimestampLikeField {
    param($Object)

    $json = ConvertTo-Json $Object -Depth 30

    $forbiddenPatterns = @(
        "timestamp",
        "captured_at",
        "created_at",
        "updated_at",
        "date_time",
        "datetime",
        "Get-Date",
        "DateTime.Now",
        "UtcNow",
        "uuid",
        "random"
    )

    foreach ($pattern in $forbiddenPatterns) {
        if ($json -match $pattern) {
            Fail "Forbidden entropy/timestamp-like token detected in receipt JSON: $pattern"
        }
    }
}

$root = Get-Location

$receiptPath = "docs/governance/receipts/slice_1_24_canonical_manifest_verification_receipt.json"
$freezePackPath = "docs/freeze_packs/slice_1_24_canonical_manifest_verification_receipt_capture.md"

Require-Path $receiptPath
Require-Path $freezePackPath

# Protected Slice 0.10 files must exist and must not be changed in working tree.
$protected = @(
    "src/smart_money/discovery/registry.py",
    "tests/discovery/test_registry.py"
)

foreach ($p in $protected) {
    Require-Path $p
}

$diffNameOnly = git diff --name-only
if ($LASTEXITCODE -ne 0) {
    Fail "git diff --name-only failed."
}

foreach ($p in $protected) {
    if ($diffNameOnly -contains $p) {
        Fail "Protected file has working-tree changes: $p"
    }
}

# Slice 1.24 must not change replay engine.
if ($diffNameOnly -contains "src/smart_money/core/replay.py") {
    Fail "Replay engine change is out of scope for Slice 1.24."
}

$raw = Get-Content -LiteralPath $receiptPath -Raw
if ([string]::IsNullOrWhiteSpace($raw)) {
    Fail "Receipt file is empty."
}

try {
    $receipt = $raw | ConvertFrom-Json -Depth 30
}
catch {
    Fail "Receipt JSON parse failed: $($_.Exception.Message)"
}

if ($null -eq $receipt.payload) {
    Fail "Missing receipt.payload."
}

if ([string]::IsNullOrWhiteSpace($receipt.receipt_sha256)) {
    Fail "Missing receipt.receipt_sha256."
}

if ($receipt.receipt_sha256 -notmatch "^[a-f0-9]{64}$") {
    Fail "receipt_sha256 must be lowercase 64-char SHA-256 hex."
}

$payload = $receipt.payload

if ($payload.receipt_schema -ne "smartmoneybotv3.canonical_manifest_verification_receipt.v1") {
    Fail "Unexpected receipt schema."
}

if ($payload.slice -ne "1.24") {
    Fail "Unexpected slice value."
}

if ($payload.title -ne "Canonical Manifest Verification Receipt Capture") {
    Fail "Unexpected title."
}

if ([string]::IsNullOrWhiteSpace($payload.base_commit)) {
    Fail "Missing base_commit."
}

if ($payload.base_commit -notmatch "^[a-f0-9]{40}$") {
    Fail "base_commit must be full 40-char lowercase git SHA."
}

if ($payload.verification.upstream_slice -ne "1.23") {
    Fail "Receipt must reference upstream Slice 1.23."
}

if ($payload.verification.verifier_exit_code -ne 0) {
    Fail "Receipt must capture verifier_exit_code = 0."
}

if ($payload.verification.verified_on_branch -ne "master") {
    Fail "Receipt must capture Slice 1.23 verification on master."
}

Assert-RelativePath $payload.verification.verifier_path
Require-Path $payload.verification.verifier_path

# Governance invariants must be explicitly true.
$requiredTrueInvariants = @(
    "em_003_status_unchanged",
    "protected_registry_unchanged",
    "protected_registry_test_unchanged",
    "no_product_logic_changed",
    "no_replay_engine_changed",
    "no_trading_or_risk_logic",
    "no_opaque_ml_decisioning",
    "no_reporting_ui_leakage",
    "receipt_has_no_promotion_authority"
)

foreach ($name in $requiredTrueInvariants) {
    $value = $payload.governance_invariants.$name
    if ($value -ne $true) {
        Fail "Governance invariant must be true: $name"
    }
}

# Validate path arrays.
if ($null -eq $payload.inputs.canonical_manifest_paths) {
    Fail "Missing inputs.canonical_manifest_paths."
}

if ($payload.inputs.canonical_manifest_paths.Count -lt 1) {
    Fail "At least one canonical manifest path is required."
}

foreach ($p in $payload.inputs.canonical_manifest_paths) {
    Assert-RelativePath $p
    Require-Path $p
}

if ($null -eq $payload.inputs.referenced_verifier_paths) {
    Fail "Missing inputs.referenced_verifier_paths."
}

foreach ($p in $payload.inputs.referenced_verifier_paths) {
    Assert-RelativePath $p
    Require-Path $p
}

foreach ($p in $payload.inputs.protected_paths) {
    Assert-RelativePath $p
    Require-Path $p
}

Assert-NoTimestampLikeField $receipt

# Recompute canonical payload hash.
$payloadJson = ConvertTo-CanonicalJson -Value $payload
$expectedHash = Get-Sha256Hex -Text $payloadJson

if ($receipt.receipt_sha256 -ne $expectedHash) {
    Fail "receipt_sha256 mismatch. Expected $expectedHash but found $($receipt.receipt_sha256)."
}

# Ensure EM-003 is not accidentally promoted by this slice.
$matrixCandidates = @(
    "docs/freeze_packs/slice_1_0_evidence_matrix.md",
    "slice_1_0_evidence_matrix.md"
)

$matrixFound = $false
foreach ($m in $matrixCandidates) {
    if (Test-Path $m) {
        $matrixFound = $true
            $lines = Get-Content -LiteralPath $m

            $em003Rows = @(
                $lines | Where-Object {
                    $_ -match '^\s*\|' -and $_ -match '\bEM-003\b'
                }
            )

            foreach ($row in $em003Rows) {
                if ($row -match '\b(LOCKED|COMPLETE|PROMOTED)\b') {
                    Fail "Potential EM-003 promotion token detected in EM-003 matrix row: $m"
                }
            }
    }
}

if (-not $matrixFound) {
    Fail "No evidence matrix candidate found."
}

Write-Host "[slice-1.24 verifier] PASS: canonical verification receipt capture is deterministic and governance-only." -ForegroundColor Green
exit 0
