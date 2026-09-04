#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location $RepoRoot

$Provider    = "src/smart_money/ingestion/provider.py"
$Tests       = "tests/ingestion/test_provider_scaffold.py"
$FreezePack  = "docs/freeze_packs/slice_1_50_ingestion_scaffold.md"
$Protected   = @(
    "src/smart_money/discovery/registry.py",
    "tests/discovery/test_registry.py"
)

# --- Existence checks ---
foreach ($f in @($Provider, $Tests, $FreezePack)) {
    if (-not (Test-Path $f)) { throw "Missing required file: $f" }
}
foreach ($f in $Protected) {
    if (-not (Test-Path $f)) { throw "Missing protected baseline file: $f" }
}

# --- Forbidden imports ---
$providerText = Get-Content $Provider -Raw
foreach ($name in @("requests","urllib","httpx","socket","subprocess","sqlite3","boto3","redis","web3")) {
    if ($providerText -match "(?m)^(from|import)\s+$name") {
        throw "Forbidden external/I/O import found in provider: $name"
    }
}

# --- Forbidden calls ---
foreach ($pattern in @("open(","Path(","urlopen(","create_connection(","subprocess.","requests.","httpx.","socket.")) {
    if ($providerText.Contains($pattern)) {
        throw "Forbidden I/O/runtime call found in provider: $pattern"
    }
}

# --- Required provider symbols ---
foreach ($symbol in @(
    "class EvidenceIngestionProvider",
    "def ingest(",
    "EvidencePayload",
    "IngestionResult",
    "get_canonical_id",
    "EvidenceGroundingLedger"
)) {
    if (-not $providerText.Contains($symbol)) {
        throw "Required provider symbol/pattern missing: $symbol"
    }
}

# --- Required test cases ---
$testText = Get-Content $Tests -Raw
foreach ($symbol in @(
    "test_deterministic_ingestion",
    "test_fail_closed_on_invalid_input",
    "test_replayability_across_instances"
)) {
    if (-not $testText.Contains($symbol)) {
        throw "Required test case missing: $symbol"
    }
}

# --- Hash protected files (before) ---
$protectedBefore = @{}
foreach ($path in $Protected) {
    $protectedBefore[$path] = (Get-FileHash $path -Algorithm SHA256).Hash
}

# --- Run pytest ---
python -m pytest tests/ingestion/test_provider_scaffold.py
if ($LASTEXITCODE -ne 0) { throw "Slice 1.50 ingestion scaffold tests failed." }

# --- Hash protected files (after) ---
foreach ($path in $Protected) {
    $after = (Get-FileHash $path -Algorithm SHA256).Hash
    if ($after -ne $protectedBefore[$path]) {
        throw "Protected file changed during verification: $path"
    }
}

Write-Output "Slice 1.50-1.52 ingestion scaffold verifier passed."
