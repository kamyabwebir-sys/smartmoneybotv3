Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail($message) {
    Write-Error "FAIL: $message"
    exit 1
}

function Require-File($path) {
    if (-not (Test-Path $path -PathType Leaf)) {
        Fail "Missing required file: $path"
    }
}

function Require-Text($path, [string[]]$tokens) {
    $text = Get-Content $path -Raw
    foreach ($token in $tokens) {
        if ($text -notmatch [regex]::Escape($token)) {
            Fail "Missing required token in ${path}: $token"
        }
    }
}

function Get-Sha256($path) {
    return (Get-FileHash -Algorithm SHA256 -Path $path).Hash.ToLowerInvariant()
}

$freezePath = "docs/freeze_packs/slice_1_27_em_003_discovery_registry_read_only_consumption_contract_lock.md"
$reviewPath = "docs/reviews/slice_1_27_em_003_discovery_registry_read_only_consumption_contract_lock_review.md"
$receiptPath = "artifacts/governance/slice_1_27_em_003_discovery_registry_read_only_consumption_contract_lock.receipt.json"

$protectedPaths = @(
    "src/smart_money/discovery/registry.py",
    "tests/discovery/test_registry.py"
)

Require-File $freezePath
Require-File $reviewPath
foreach ($path in $protectedPaths) { Require-File $path }

Require-Text $freezePath @(
    "Slice 1.27",
    "Read-Only Consumption Contract Lock",
    "Governance and documentation lock only",
    "Deterministic, replayable, fail-closed",
    "read-only evidence metadata",
    "canonical evidence identity",
    "evidence case metadata",
    "deterministic registry references",
    "replay/audit grounding references",
    "execution logic",
    "trading logic",
    "risk calculation",
    "opaque ML decisioning",
    "reporting/UI leakage into core/domain logic",
    "mutation of registry state",
    "src/smart_money/discovery/registry.py",
    "tests/discovery/test_registry.py"
)

Require-Text $reviewPath @(
    "Review Verdict: APPROVED_FOR_VERIFICATION",
    "governance-only",
    "Protected Path Review",
    "Determinism Review",
    "CLOSED / PASS"
)

if (-not (Test-Path ".git" -PathType Container)) {
    Fail "Git metadata is required to verify protected paths fail-closed."
}

$gitStatus = git status --porcelain -- $protectedPaths 2>$null
if ($LASTEXITCODE -ne 0) {
    Fail "Unable to inspect protected path git status."
}
if (-not [string]::IsNullOrWhiteSpace(($gitStatus | Out-String))) {
    Fail "Protected registry paths are modified or untracked."
}

$artifactDir = Split-Path -Parent $receiptPath
if (-not (Test-Path $artifactDir)) {
    New-Item -ItemType Directory -Path $artifactDir | Out-Null
}

$receipt = [ordered]@{
    slice = "1.27"
    status = "PASS"
    authority_scope = "governance_and_documentation_lock_only"
    verification_mode = "deterministic_replayable_fail_closed"
    evidence_class = "read_only_downstream_consumption_contract"
    receipt_path = $receiptPath
    freeze_pack = @{
        path = $freezePath
        sha256 = Get-Sha256 $freezePath
    }
    review = @{
        path = $reviewPath
        sha256 = Get-Sha256 $reviewPath
    }
    protected_paths = @(
        @{
            path = "src/smart_money/discovery/registry.py"
            sha256 = Get-Sha256 "src/smart_money/discovery/registry.py"
        },
        @{
            path = "tests/discovery/test_registry.py"
            sha256 = Get-Sha256 "tests/discovery/test_registry.py"
        }
    )
    guardrails = @{
        read_only_registry_consumption = $true
        no_execution_logic = $true
        no_trading_logic = $true
        no_risk_calculation = $true
        no_opaque_ml_decisioning = $true
        no_reporting_ui_leakage = $true
        registry_mutation_allowed = $false
    }
}

$json = $receipt | ConvertTo-Json -Depth 8
Set-Content -Path $receiptPath -Value $json -Encoding utf8NoBOM

$roundTrip = Get-Content $receiptPath -Raw | ConvertFrom-Json
if ($roundTrip.slice -ne "1.27") { Fail "Receipt slice mismatch." }
if ($roundTrip.status -ne "PASS") { Fail "Receipt status mismatch." }

Write-Host "PASS Slice 1.27 verifier"
Write-Host "Receipt: $receiptPath"
exit 0
