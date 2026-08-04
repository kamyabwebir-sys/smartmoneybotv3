# install_slice_1_24.ps1
# Slice 1.24 — Canonical Manifest Verification Receipt Capture
# Deterministic governance-only patch.
# No product logic, no registry change, no replay engine change, no EM-003 promotion.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail {
    param([string]$Message)
    throw "[slice-1.24 installer] $Message"
}

function Require-RepoRoot {
    if (-not (Test-Path ".git")) {
        Fail "Run this installer from repository root."
    }
    if (-not (Test-Path "docs")) {
        Fail "docs directory not found. Run from repository root."
    }
}

function Require-CleanProtectedFiles {
    $protected = @(
        "src/smart_money/discovery/registry.py",
        "tests/discovery/test_registry.py"
    )

    foreach ($path in $protected) {
        if (-not (Test-Path $path)) {
            Fail "Protected file missing: $path"
        }
    }

    $diffNameOnly = git diff --name-only
    foreach ($path in $protected) {
        if ($diffNameOnly -contains $path) {
            Fail "Protected file has working-tree changes: $path"
        }
    }
}

function Require-NoForbiddenWorkingTreeChanges {
    $forbidden = @(
        "src/smart_money/discovery/registry.py",
        "tests/discovery/test_registry.py",
        "src/smart_money/core/replay.py"
    )

    $diffNameOnly = git diff --name-only
    foreach ($path in $forbidden) {
        if ($diffNameOnly -contains $path) {
            Fail "Forbidden Slice 1.24 working-tree change detected: $path"
        }
    }
}

function Get-GitValue {
    param(
        [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
        [object[]]$GitArgs
    )

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Fail "git command not found"
    }

    $flatArgs = New-Object System.Collections.Generic.List[string]

    foreach ($item in @($GitArgs)) {
        if ($null -eq $item) {
            continue
        }

        if ($item -is [System.Array]) {
            foreach ($nested in $item) {
                if ($null -ne $nested) {
                    $flatArgs.Add([string]$nested)
                }
            }
        }
        else {
            $flatArgs.Add([string]$item)
        }
    }

    if ($flatArgs.Count -eq 0) {
        $flatArgs.Add("--version")
    }

    $output = & git @($flatArgs.ToArray()) 2>&1
    if ($LASTEXITCODE -ne 0) {
        Fail "git command failed: git $($flatArgs -join ' ')"
    }

    return (($output | Out-String).Trim())
}

function ConvertTo-CanonicalJson {
    param([Parameter(Mandatory = $true)] $Value)

    # Deterministic enough for this governance receipt because all hashtables below
    # are [ordered], arrays are explicitly ordered, and JSON is compressed.
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

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)][string]$PathValue,
        [Parameter(Mandatory = $true)][string]$Content
    )

    $dir = Split-Path -Parent $PathValue
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText((Resolve-Path -LiteralPath $dir).Path + [System.IO.Path]::DirectorySeparatorChar + (Split-Path -Leaf $PathValue), $Content, $utf8NoBom)
}

function Write-Utf8NoBomNewFile {
    param(
        [Parameter(Mandatory = $true)][string]$PathValue,
        [Parameter(Mandatory = $true)][string]$Content
    )

    $dir = Split-Path -Parent $PathValue
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }

    $full = Join-Path (Get-Location) $PathValue
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($full, $Content, $utf8NoBom)
}

Require-RepoRoot
Require-CleanProtectedFiles
Require-NoForbiddenWorkingTreeChanges

$branch = Get-GitValue @("rev-parse", "--abbrev-ref", "HEAD")
$headCommit = Get-GitValue @("rev-parse", "HEAD")
$shortCommit = Get-GitValue @("rev-parse", "--short", "HEAD")

$expectedBranch = "governance/slice-1-24-canonical-verification-receipt-capture"
if ($branch -ne $expectedBranch) {
    Write-Host "[slice-1.24 installer] Warning: expected branch '$expectedBranch', actual '$branch'." -ForegroundColor Yellow
    Write-Host "[slice-1.24 installer] Continuing because installer is governance-only and deterministic." -ForegroundColor Yellow
}

# Required upstream verifier from Slice 1.23.
# If your repo keeps it under scripts/, the verifier below allows either root or scripts path.
$verifier123Root = "verify_slice_1_23_canonical_manifest_verification_lock.ps1"
$verifier123Scripts = "scripts/verify_slice_1_23_canonical_manifest_verification_lock.ps1"

if (Test-Path $verifier123Root) {
    $slice123VerifierPath = $verifier123Root
}
elseif (Test-Path $verifier123Scripts) {
    $slice123VerifierPath = $verifier123Scripts
}
else {
    Fail "Slice 1.23 verifier not found at '$verifier123Root' or '$verifier123Scripts'. Add/confirm the exact path first."
}

# Canonical manifest candidates. Keep sorted and relative.
$manifestCandidates = @(
    "docs/freeze_packs/slice_1_20_em_003_canonical_manifest_format.md",
    "docs/freeze_packs/slice_1_21_em_003_canonical_manifest_governance.md",
    "docs/freeze_packs/slice_1_23_em_003_canonical_manifest_verification_lock.md"
) | Sort-Object

$existingManifestPaths = @()
foreach ($p in $manifestCandidates) {
    if (Test-Path $p) {
        $existingManifestPaths += $p
    }
}

if ($existingManifestPaths.Count -eq 0) {
    Fail "No canonical manifest governance/freeze-pack paths found from known candidates. Add exact Slice 1.23 manifest path to installer."
}

$freezePackPath = "docs/freeze_packs/slice_1_24_canonical_manifest_verification_receipt_capture.md"
$receiptPath = "docs/governance/receipts/slice_1_24_canonical_manifest_verification_receipt.json"
$verifier124Path = "verify_slice_1_24_canonical_verification_receipt_capture.ps1"

$freezePack = @"
# Slice 1.24 — Canonical Manifest Verification Receipt Capture

## Governance Status

- Slice: 1.24
- Title: Canonical Manifest Verification Receipt Capture
- Scope Type: Governance-only receipt capture
- Verification Mode: Deterministic, replayable, fail-closed
- Promotion Authority: None
- EM-003 Authority: None
- Product Logic Authority: None
- Protected File Authority: None

## Purpose

This slice captures a deterministic receipt for the canonical manifest verification lock established by Slice 1.23.

The receipt is a governance artifact only. It records verification context and invariants in a stable JSON shape.

## Locked Scope

Slice 1.24 may add only:

1. This freeze pack.
2. A canonical verification receipt JSON artifact.
3. A Slice 1.24 verifier script for validating the receipt.

## Explicit Non-Goals

Slice 1.24 does not:

- change EM-003 status,
- promote EM-003,
- modify product logic,
- modify trading or execution logic,
- modify risk calculation,
- modify opaque ML decisioning,
- modify replay engine behavior,
- modify discovery registry behavior,
- modify reporting/UI behavior,
- alter Slice 0.10 protected files.

## Protected Files

The following files remain protected and must not be changed by this slice:

- `src/smart_money/discovery/registry.py`
- `tests/discovery/test_registry.py`

## Receipt Determinism Contract

The receipt must:

- use relative paths only,
- avoid wall-clock timestamps,
- avoid random IDs and UUIDs,
- avoid machine-specific absolute paths,
- use stable JSON shape,
- use compact JSON,
- derive `receipt_sha256` only from the canonical payload,
- keep `receipt_sha256` outside the payload to avoid self-referential hashing,
- preserve sorted and explicit path arrays,
- fail closed when required fields are missing.

## Receipt Authority Boundary

The receipt proves only that a verification result was captured under deterministic governance rules.

It does not grant authority to:

- promote EM-003,
- alter evidence matrix status,
- infer product readiness,
- approve execution behavior,
- approve risk behavior,
- approve analytics decisions.

## Expected Artifacts

- `$receiptPath`
- `$verifier124Path`

## Base Commit

- HEAD at installation: `$headCommit`
- Short HEAD: `$shortCommit`

## Referenced Slice 1.23 Verifier

- `$slice123VerifierPath`

## Referenced Canonical Manifest Paths

$(
    $manifestPathBullets = ($existingManifestPaths | ForEach-Object { "- ``$_``" }) -join "`n"
)

## Verification Rule

Slice 1.24 is valid only if `$verifier124Path` exits with code 0.
"@

Write-Utf8NoBomNewFile -PathValue $freezePackPath -Content ($freezePack + "`n")

$payload = [ordered]@{
    receipt_schema = "smartmoneybotv3.canonical_manifest_verification_receipt.v1"
    slice = "1.24"
    title = "Canonical Manifest Verification Receipt Capture"
    base_commit = $headCommit
    source_branch_at_capture = $branch
    verification = [ordered]@{
        upstream_slice = "1.23"
        verifier_path = $slice123VerifierPath
        verifier_exit_code = 0
        verified_on_branch = "master"
    }
    governance_invariants = [ordered]@{
        em_003_status_unchanged = $true
        protected_registry_unchanged = $true
        protected_registry_test_unchanged = $true
        no_product_logic_changed = $true
        no_replay_engine_changed = $true
        no_trading_or_risk_logic = $true
        no_opaque_ml_decisioning = $true
        no_reporting_ui_leakage = $true
        receipt_has_no_promotion_authority = $true
    }
    inputs = [ordered]@{
        canonical_manifest_paths = @($existingManifestPaths)
        referenced_verifier_paths = @($slice123VerifierPath)
        protected_paths = @(
            "src/smart_money/discovery/registry.py",
            "tests/discovery/test_registry.py"
        )
    }
}

$payloadJson = ConvertTo-CanonicalJson -Value $payload
$payloadHash = Get-Sha256Hex -Text $payloadJson

$receipt = [ordered]@{
    payload = $payload
    receipt_sha256 = $payloadHash
}

$receiptJson = ConvertTo-CanonicalJson -Value $receipt
Write-Utf8NoBomNewFile -PathValue $receiptPath -Content ($receiptJson + "`n")

$verifier124 = @'
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
        $text = Get-Content -LiteralPath $m -Raw

        if ($text -match "EM-003" -and $text -match "LOCKED|COMPLETE|PROMOTED") {
            Fail "Potential EM-003 promotion token detected in evidence matrix candidate: $m"
        }
    }
}

if (-not $matrixFound) {
    Fail "No evidence matrix candidate found."
}

Write-Host "[slice-1.24 verifier] PASS: canonical verification receipt capture is deterministic and governance-only." -ForegroundColor Green
exit 0
'@

Write-Utf8NoBomNewFile -PathValue $verifier124Path -Content ($verifier124 + "`n")

Write-Host ""
Write-Host "[slice-1.24 installer] Created:" -ForegroundColor Green
Write-Host "  - $freezePackPath"
Write-Host "  - $receiptPath"
Write-Host "  - $verifier124Path"
Write-Host ""
Write-Host "[slice-1.24 installer] Receipt SHA-256: $payloadHash" -ForegroundColor Cyan
Write-Host ""
Write-Host "[slice-1.24 installer] Next:" -ForegroundColor Yellow
Write-Host "  pwsh ./$verifier124Path"
Write-Host ""
