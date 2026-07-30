$ErrorActionPreference = "Stop"

function Fail($Message) {
    Write-Host "FAIL-CLOSED: $Message" -ForegroundColor Red
    exit 1
}

function Pass($Message) {
    Write-Host "PASS: $Message" -ForegroundColor Green
}

function Normalize-PathForGovernance($Path) {
    return ($Path -replace "\\", "/").Trim()
}

$FreezePackPath = "docs/freeze_packs/slice_1_17_em_003_separate_promotion_authority_request_gate.md"
$ReviewPath = "docs/reviews/slice_1_17_em_003_separate_promotion_authority_request_gate_review.md"
$EvidenceReportPath = "artifacts/discovery/em003/evidence_report.json"

if (-not (Test-Path $FreezePackPath)) {
    Fail "Missing Slice 1.17 freeze pack: $FreezePackPath"
}

if (-not (Test-Path $ReviewPath)) {
    Fail "Missing Slice 1.17 review: $ReviewPath"
}

if (-not (Test-Path $EvidenceReportPath)) {
    Fail "Missing EM-003 evidence report: $EvidenceReportPath"
}

$FreezePack = Get-Content $FreezePackPath -Raw
$Review = Get-Content $ReviewPath -Raw
$EvidenceReportRaw = Get-Content $EvidenceReportPath -Raw

try {
    $EvidenceReport = $EvidenceReportRaw | ConvertFrom-Json
} catch {
    Fail "evidence_report.json is not valid JSON."
}

if ($EvidenceReport.em_id -ne "EM-003") {
    Fail "Unexpected em_id. Expected EM-003, found: $($EvidenceReport.em_id)"
}

if ($EvidenceReport.status -ne "PARTIAL") {
    Fail "EM-003 must remain PARTIAL. Found: $($EvidenceReport.status)"
}

if ($EvidenceReport.promotion_gate -ne "LOCKED") {
    Fail "Promotion gate must remain LOCKED. Found: $($EvidenceReport.promotion_gate)"
}

if ($EvidenceReport.implementation_authority -ne "NONE") {
    Fail "Implementation authority must remain NONE. Found: $($EvidenceReport.implementation_authority)"
}

if ($EvidenceReport.approval_status -ne "NOT_APPROVED") {
    Fail "Approval status must remain NOT_APPROVED. Found: $($EvidenceReport.approval_status)"
}

if ($null -eq $EvidenceReport.deterministic) {
    Fail "Evidence report must include deterministic field."
}

if ($EvidenceReport.deterministic -ne $true) {
    Fail "Evidence report deterministic field must be true for governance review."
}

if ($null -eq $EvidenceReport.replayable) {
    Fail "Evidence report must include replayable field."
}

if ($EvidenceReport.replayable -ne $true) {
    Fail "Evidence report replayable field must be true for governance review."
}

if ($FreezePack -notlike "*governance-only*") {
    Fail "Freeze pack must explicitly state governance-only."
}

if ($Review -notlike "*governance-only*") {
    Fail "Review must explicitly state governance-only."
}

if ($Review -notlike "*EM-003 remains PARTIAL*") {
    Fail "Review must explicitly state EM-003 remains PARTIAL."
}

if (($Review -notlike "*Promotion remains blocked*") -and ($Review -notlike "*Promotion remains LOCKED*")) {
    Fail "Review must explicitly preserve blocked or locked promotion posture."
}

if ($Review -notlike "*Implementation authority remains NONE*") {
    Fail "Review must explicitly state implementation authority remains NONE."
}

if ($Review -notlike "*Approval status remains NOT_APPROVED*") {
    Fail "Review must explicitly state approval status remains NOT_APPROVED."
}

$AllowedVerdicts = @(
    "AUTHORITY_REQUEST_DENIED_FAIL_CLOSED",
    "AUTHORITY_REQUEST_READY_FOR_SEPARATE_HUMAN_APPROVAL"
)

$VerdictMatches = @()
foreach ($Verdict in $AllowedVerdicts) {
    if ($Review -like "*$Verdict*") {
        $VerdictMatches += $Verdict
    }
}

if ($VerdictMatches.Count -ne 1) {
    Fail "Review must contain exactly one allowed authority request verdict."
}

$SelectedVerdict = $VerdictMatches[0]

$CasesMissingOrEmpty = $false

if ($null -eq $EvidenceReport.cases) {
    $CasesMissingOrEmpty = $true
} elseif ($EvidenceReport.cases.Count -eq 0) {
    $CasesMissingOrEmpty = $true
}

if ($CasesMissingOrEmpty -and $SelectedVerdict -ne "AUTHORITY_REQUEST_DENIED_FAIL_CLOSED") {
    Fail "Missing or empty case population requires AUTHORITY_REQUEST_DENIED_FAIL_CLOSED."
}

if ($CasesMissingOrEmpty -and $Review -notlike "*current evidence case population is empty or incomplete*") {
    Fail "Review must explain that current evidence case population is empty or incomplete."
}

if ($SelectedVerdict -eq "AUTHORITY_REQUEST_READY_FOR_SEPARATE_HUMAN_APPROVAL") {
    if ($CasesMissingOrEmpty) {
        Fail "Request-ready verdict is not allowed with missing or empty evidence cases."
    }

    foreach ($Case in $EvidenceReport.cases) {
        if ($null -eq $Case.case_id) {
            Fail "Every evidence case must include case_id for request-ready verdict."
        }

        if ($null -eq $Case.status) {
            Fail "Every evidence case must include status for request-ready verdict."
        }

        if ($Case.status -eq "PARTIAL") {
            Fail "Request-ready verdict is not allowed when any evidence case is PARTIAL."
        }

        if ($Case.status -eq "MISSING") {
            Fail "Request-ready verdict is not allowed when any evidence case is MISSING."
        }

        if ($Case.status -eq "FAILED") {
            Fail "Request-ready verdict is not allowed when any evidence case is FAILED."
        }
    }
}

$ForbiddenReviewPhrases = @(
    "approved promotion",
    "promotion granted",
    "authority granted",
    "gate unlocked",
    "status promoted",
    "status changed"
)

foreach ($Phrase in $ForbiddenReviewPhrases) {
    if ($Review -like "*$Phrase*") {
        Fail "Forbidden review phrase detected: $Phrase"
    }
}

$ForbiddenFreezePackPhrases = @(
    "approved promotion",
    "promotion granted",
    "authority granted",
    "gate unlocked",
    "status promoted",
    "status changed"
)

foreach ($Phrase in $ForbiddenFreezePackPhrases) {
    if ($FreezePack -like "*$Phrase*") {
        Fail "Forbidden freeze pack phrase detected: $Phrase"
    }
}

$ProtectedPaths = @(
    "src/smart_money/discovery/registry.py",
    "tests/discovery/test_registry.py"
)

$ForbiddenChangedPrefixes = @(
    "src/",
    "tests/"
)

$ChangedFiles = @()

try {
    $GitAvailable = $true
    git rev-parse --is-inside-work-tree *> $null
    if ($LASTEXITCODE -ne 0) {
        $GitAvailable = $false
    }

    if ($GitAvailable) {
        $ChangedFiles = git diff --name-only
        $StagedFiles = git diff --cached --name-only
        $UntrackedFiles = git ls-files --others --exclude-standard

        if ($null -ne $StagedFiles) {
            $ChangedFiles += $StagedFiles
        }

        if ($null -ne $UntrackedFiles) {
            $ChangedFiles += $UntrackedFiles
        }

        $ChangedFiles = $ChangedFiles | Where-Object { $_ -ne $null -and $_.Trim() -ne "" } | Sort-Object -Unique
    }
} catch {
    Write-Host "WARN: Git change inspection unavailable; continuing with artifact-level checks only." -ForegroundColor Yellow
    $ChangedFiles = @()
}

foreach ($Changed in $ChangedFiles) {
    $Normalized = Normalize-PathForGovernance $Changed

    foreach ($ProtectedPath in $ProtectedPaths) {
        if ($Normalized -eq $ProtectedPath) {
            Fail "Protected registry path change detected: $Normalized"
        }
    }

    foreach ($Prefix in $ForbiddenChangedPrefixes) {
        if ($Normalized.StartsWith($Prefix)) {
            Fail "Unauthorized src/tests change detected: $Normalized"
        }
    }
}

foreach ($Changed in $ChangedFiles) {
    $Normalized = Normalize-PathForGovernance $Changed

    if ($Normalized -like "docs/freeze_packs/slice_1_17_*") {
        continue
    }

    if ($Normalized -like "docs/reviews/slice_1_17_*") {
        continue
    }

    if ($Normalized -like "scripts/verify_slice_1_17_*") {
        continue
    }

    if ($Normalized -eq "scripts/install_slice_1_17.ps1") {
        continue
    }

    if ($Normalized.StartsWith("src/") -or $Normalized.StartsWith("tests/")) {
        Fail "Unauthorized implementation/test change detected: $Normalized"
    }
}

Pass "Slice 1.17 authority request gate remains governance-only, fail-closed, and PARTIAL-preserving."