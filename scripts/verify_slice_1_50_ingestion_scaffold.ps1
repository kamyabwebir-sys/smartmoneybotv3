#requires -Version 7.0

[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = (Resolve-Path $RepoRoot).Path
Set-Location $RepoRoot

$Provider = Join-Path $RepoRoot "src/smart_money/ingestion/provider.py"
$Tests = Join-Path $RepoRoot "tests/ingestion/test_provider_scaffold.py"
$FreezePack = Join-Path $RepoRoot "docs/freeze_packs/slice_1_50_ingestion_scaffold.md"

$Protected = @(
    (Join-Path $RepoRoot "src/smart_money/discovery/registry.py"),
    (Join-Path $RepoRoot "tests/discovery/test_registry.py")
)

foreach ($path in @($Provider, $Tests, $FreezePack)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing required file: $path"
    }
}

foreach ($path in $Protected) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing protected baseline file: $path"
    }
}

$providerText = Get-Content -LiteralPath $Provider -Raw
$testText = Get-Content -LiteralPath $Tests -Raw

$forbiddenImports = @(
    "requests",
    "urllib",
    "httpx",
    "socket",
    "subprocess",
    "sqlite3",
    "boto3",
    "redis",
    "web3"
)

foreach ($name in $forbiddenImports) {
    if ($providerText -match "(?m)^\s*(from|import)\s+$name(\.|\s|$)") {
        throw "Forbidden external/I/O import found in provider: $name"
    }
}

$forbiddenCalls = @(
    "open(",
    "Path(",
    "urlopen(",
    "create_connection(",
    "subprocess.",
    "requests.",
    "httpx.",
    "socket."
)

foreach ($pattern in $forbiddenCalls) {
    if ($providerText.Contains($pattern)) {
        throw "Forbidden I/O/runtime call found in provider: $pattern"
    }
}

$requiredProviderSymbols = @(
    "class EvidenceIngestionProvider",
    "def ingest(",
    "EvidencePayload",
    "IngestionResult",
    "get_canonical_id",
    "EvidenceGroundingLedger"
)

foreach ($symbol in $requiredProviderSymbols) {
    if (-not $providerText.Contains($symbol)) {
        throw "Required provider symbol/pattern missing: $symbol"
    }
}

$requiredTestSymbols = @(
    "test_deterministic_ingestion",
    "test_fail_closed_on_invalid_input",
    "test_replayability_across_instances"
)

foreach ($symbol in $requiredTestSymbols) {
    if (-not $testText.Contains($symbol)) {
        throw "Required test case missing: $symbol"
    }
}

$protectedBefore = @{}

foreach ($path in $Protected) {
    $protectedBefore[$path] = (
        Get-FileHash -LiteralPath $path -Algorithm SHA256
    ).Hash
}

python -m pytest tests/ingestion/test_provider_scaffold.py

if ($LASTEXITCODE -ne 0) {
    throw "Slice 1.50 ingestion scaffold tests failed."
}

foreach ($path in $Protected) {
    $after = (
        Get-FileHash -LiteralPath $path -Algorithm SHA256
    ).Hash

    if ($after -ne $protectedBefore[$path]) {
        throw "Protected file changed during verification: $path"
    }
}

Write-Output "Slice 1.50–1.52 ingestion scaffold verifier passed."
