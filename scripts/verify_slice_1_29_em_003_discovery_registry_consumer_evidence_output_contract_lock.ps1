Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$sliceId = "slice_1_29_em_003_discovery_registry_consumer_evidence_output_contract_lock"

$freezePackPath = ".\docs\freeze_packs\$sliceId.md"
$reviewPath = ".\docs\reviews\${sliceId}_review.md"
$verifierPath = ".\scripts\verify_${sliceId}.ps1"
$receiptPath = ".\artifacts\governance\$sliceId.receipt.json"

$protectedHashesExpected = [ordered]@{
    ".\src\smart_money\discovery\registry.py" = "744c4cc809794efb455f209f9857ed0f89a5a97f135e872b0f014f50082742d7"
    ".\tests\discovery\test_registry.py" = "a68aa20a90826aed09e4bcd61837499583cac5401372a1fbc587de9b636ed26a"
}

function Fail {
    param([Parameter(Mandatory = $true)][string]$Message)

    $receipt = [ordered]@{
        schema_version = "governance.receipt.v1"
        slice_id = $sliceId
        status = "FAIL"
        reason = $Message
        generated_at_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    }

    $dir = Split-Path -Parent $receiptPath
    if ($dir -and -not (Test-Path $dir -PathType Container)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
    }

    $receipt | ConvertTo-Json -Depth 8 | Set-Content -Path $receiptPath -Encoding utf8NoBOM
    throw $Message
}

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path $Path -PathType Leaf)) {
        Fail "Missing protected path: ${Path}"
    }

    return (Get-FileHash -Algorithm SHA256 -Path $Path).Hash.ToLowerInvariant()
}

function Require-File {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path $Path -PathType Leaf)) {
        Fail "Missing required file: ${Path}"
    }
}

function Require-Token {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Token
    )

    $text = Get-Content -Path $Path -Raw
    if (-not $text.Contains($Token)) {
        Fail "Missing required token in ${Path}: $Token"
    }
}

Require-File -Path $freezePackPath
Require-File -Path $reviewPath
Require-File -Path $verifierPath

foreach ($protectedPath in $protectedHashesExpected.Keys) {
    $actual = Get-Sha256 -Path $protectedPath
    $expected = $protectedHashesExpected[$protectedPath]

    if ([string]::IsNullOrWhiteSpace($expected) -or $expected.StartsWith("__")) {
        Fail "Verifier contains unresolved protected hash placeholder for ${protectedPath}"
    }

    if ($actual -ne $expected) {
        Fail "Protected path hash changed: ${protectedPath}"
    }
}

$requiredFreezeTokens = @(
    "Slice 1.29 - EM-003 Discovery Registry Consumer Evidence Output Contract Lock",
    "Slice Type: Governance-only",
    "Verifier Mode: Fail-closed",
    "Evidence-only: output may describe evidence and score breakdown, not decisions.",
    "Deterministic: identical registry input and consumer version yield identical evidence output.",
    "Replayable: output must retain stable references to registry input and replay manifest identity.",
    "Read-only: output generation must not mutate registry content.",
    "Boundary-safe: output must not leak execution, risk, opaque ML decisioning, reporting, or UI behavior into core/domain logic.",
    "Auditable: output must contain enough stable references for later verifier inspection.",
    "trade execution instruction",
    "position sizing",
    "opaque ML decision",
    "src/smart_money/discovery/registry.py",
    "tests/discovery/test_registry.py"
)

$requiredReviewTokens = @(
    "Verdict: PASS-CANDIDATE",
    "Scope: Governance-only",
    "Protected Paths: UNCHANGED REQUIRED",
    "Execution Logic: NOT ALLOWED",
    "Risk Calculation: NOT ALLOWED",
    "Opaque ML Decisioning: NOT ALLOWED",
    "Reporting/UI Leakage: NOT ALLOWED",
    "Approve as CLOSED / PASS"
)

foreach ($token in $requiredFreezeTokens) {
    Require-Token -Path $freezePackPath -Token $token
}

foreach ($token in $requiredReviewTokens) {
    Require-Token -Path $reviewPath -Token $token
}

$receipt = [ordered]@{
    schema_version = "governance.receipt.v1"
    slice_id = $sliceId
    status = "PASS"
    verifier = $verifierPath
    freeze_pack = $freezePackPath
    review = $reviewPath
    protected_paths = @(
        [ordered]@{
            path = ".\src\smart_money\discovery\registry.py"
            sha256 = $protectedHashesExpected[".\src\smart_money\discovery\registry.py"]
            status = "UNCHANGED"
        },
        [ordered]@{
            path = ".\tests\discovery\test_registry.py"
            sha256 = $protectedHashesExpected[".\tests\discovery\test_registry.py"]
            status = "UNCHANGED"
        }
    )
    locked_contract = [ordered]@{
        registry_consumption = "READ_ONLY"
        consumer_interface_shape = "PREVIOUSLY_LOCKED_BY_SLICE_1_28"
        evidence_output_contract = "LOCKED"
        analytics_output = "EVIDENCE_AND_SCORE_BREAKDOWN_ONLY"
        execution_logic = "FORBIDDEN"
        order_intent = "FORBIDDEN"
        position_sizing = "FORBIDDEN"
        risk_calculation = "FORBIDDEN"
        opaque_ml_decisioning = "FORBIDDEN"
        reporting_ui_leakage = "FORBIDDEN"
        replay_traceability = "REQUIRED"
        deterministic_output = "REQUIRED"
    }
    generated_at_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}

$dir = Split-Path -Parent $receiptPath
if ($dir -and -not (Test-Path $dir -PathType Container)) {
    New-Item -ItemType Directory -Path $dir | Out-Null
}

$receipt | ConvertTo-Json -Depth 12 | Set-Content -Path $receiptPath -Encoding utf8NoBOM

Write-Host "Slice 1.29 verifier PASS"
Write-Host "Receipt: $receiptPath"
