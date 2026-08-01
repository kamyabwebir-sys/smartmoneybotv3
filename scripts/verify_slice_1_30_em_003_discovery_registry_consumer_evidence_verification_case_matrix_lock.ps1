Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$sliceId = "slice_1_30_em_003_discovery_registry_consumer_evidence_verification_case_matrix_lock"

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
    "Slice 1.30 - EM-003 Discovery Registry Consumer Evidence Verification Case Matrix Lock",
    "Slice Type: Governance-only",
    "Verifier Mode: Fail-closed",
    "EM003-CONS-EV-001",
    "EM003-CONS-EV-002",
    "EM003-CONS-EV-003",
    "EM003-CONS-EV-004",
    "EM003-CONS-EV-005",
    "EM003-CONS-EV-006",
    "EM003-CONS-EV-007",
    "EM003-CONS-EV-008",
    "EM003-CONS-EV-009",
    "EM003-CONS-EV-010",
    "EM003-CONS-EV-011",
    "EM003-CONS-EV-012",
    "EM003-CONS-EV-013",
    "EM003-CONS-EV-014",
    "EM003-CONS-EV-015",
    "output is evidence-only",
    "output is deterministic",
    "output is replayable",
    "output is read-only",
    "output is auditable",
    "execution/trading logic",
    "risk calculation",
    "opaque ML decisioning",
    "reporting/UI leakage",
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
        previous_contract = "SLICE_1_29_EVIDENCE_OUTPUT_CONTRACT_LOCK"
        verification_case_matrix = "LOCKED"
        required_pass_cases = @(
            "EM003-CONS-EV-001",
            "EM003-CONS-EV-002",
            "EM003-CONS-EV-003",
            "EM003-CONS-EV-004",
            "EM003-CONS-EV-005"
        )
        required_fail_cases = @(
            "EM003-CONS-EV-006",
            "EM003-CONS-EV-007",
            "EM003-CONS-EV-008",
            "EM003-CONS-EV-009",
            "EM003-CONS-EV-010",
            "EM003-CONS-EV-011",
            "EM003-CONS-EV-012",
            "EM003-CONS-EV-013",
            "EM003-CONS-EV-014",
            "EM003-CONS-EV-015"
        )
        execution_logic = "FORBIDDEN"
        order_intent = "FORBIDDEN"
        position_sizing = "FORBIDDEN"
        risk_calculation = "FORBIDDEN"
        opaque_ml_decisioning = "FORBIDDEN"
        reporting_ui_leakage = "FORBIDDEN"
        replay_traceability = "REQUIRED"
        deterministic_output = "REQUIRED"
        fail_closed_future_verifier = "REQUIRED"
    }
    generated_at_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}

$dir = Split-Path -Parent $receiptPath
if ($dir -and -not (Test-Path $dir -PathType Container)) {
    New-Item -ItemType Directory -Path $dir | Out-Null
}

$receipt | ConvertTo-Json -Depth 12 | Set-Content -Path $receiptPath -Encoding utf8NoBOM

Write-Host "Slice 1.30 verifier PASS"
Write-Host "Receipt: $receiptPath"
