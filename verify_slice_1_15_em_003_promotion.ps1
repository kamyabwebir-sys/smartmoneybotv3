Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail {
    param([string] $Message)
    Write-Error $Message
    exit 1
}

function Resolve-FirstExisting {
    param([string[]] $CandidatePaths)

    foreach ($Path in $CandidatePaths) {
        if (Test-Path -LiteralPath $Path) {
            return (Resolve-Path -LiteralPath $Path).Path
        }
    }

    Fail ("Required artifact not found. Checked: " + ($CandidatePaths -join ", "))
}

function Assert-Contains {
    param(
        [string] $Content,
        [string] $Needle,
        [string] $Context
    )

    if (-not $Content.Contains($Needle)) {
        Fail "Missing required text in ${Context}: ${Needle}"
    }
}

function Get-MarkdownRows {
    param([string] $Content)

    $Rows = @()
    foreach ($Line in ($Content -split "`r?`n")) {
        $Trimmed = $Line.Trim()
        if (-not $Trimmed.StartsWith("|") -or -not $Trimmed.EndsWith("|")) { continue }

        $Inner = $Trimmed.Trim([char]'|').Trim()
        if ($Inner -match '^[\s:\-\|]+$') { continue }

        $Cells = @()
        foreach ($Cell in $Trimmed.Trim([char]'|').Split([char]'|')) {
            $Cells += $Cell.Trim()
        }

        $Rows += ,$Cells
    }

    return $Rows
}

function Get-Em003Row {
    param([string] $Content)

    foreach ($Cells in (Get-MarkdownRows $Content)) {
        if ($Cells.Count -ge 4 -and $Cells[0] -eq "EM-003") {
            return $Cells
        }
    }

    Fail "EM-003 row not found in official evidence matrix."
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

$MatrixPath = Resolve-FirstExisting @(
    (Join-Path $Root "docs/freeze_packs/slice_1_0_evidence_matrix.md"),
    (Join-Path $Root "slice_1_0_evidence_matrix.md")
)
$GovernancePath = Resolve-FirstExisting @(
    (Join-Path $Root "docs/freeze_packs/slice_1_15_em_003_promotion_governance_event.md"),
    (Join-Path $Root "slice_1_15_em_003_promotion_governance_event.md")
)
$ReviewPath = Resolve-FirstExisting @(
    (Join-Path $Root "docs/reviews/slice_1_15_em_003_promotion_review.md"),
    (Join-Path $Root "slice_1_15_em_003_promotion_review.md")
)
$Grant14Path = Resolve-FirstExisting @(
    (Join-Path $Root "docs/freeze_packs/slice_1_14_em_003_limited_verifier_authority_grant.md"),
    (Join-Path $Root "slice_1_14_em_003_limited_verifier_authority_grant.md")
)

$Matrix = Get-Content -LiteralPath $MatrixPath -Raw
$Governance = Get-Content -LiteralPath $GovernancePath -Raw
$Review = Get-Content -LiteralPath $ReviewPath -Raw
$Grant14 = Get-Content -LiteralPath $Grant14Path -Raw

$Row = Get-Em003Row $Matrix
$Status = $Row[3]

if ($Status -ne "GROUNDED") {
    Fail "Slice 1.15 requires official EM-003 matrix status GROUNDED, found '$Status'."
}

Assert-Contains $Governance "Slice 1.15 records the explicit governance event" $GovernancePath
Assert-Contains $Governance "Those artifacts remain immutable governance snapshots" $GovernancePath
Assert-Contains $Governance "No execution logic, trading logic, risk calculation, opaque ML decisioning, protected registry mutation, or reporting/UI leakage is introduced" $GovernancePath
Assert-Contains $Review "APPROVED_FOR_PROMOTION" $ReviewPath
Assert-Contains $Review "EM-003 is accepted as GROUNDED under Slice 1.15 authority" $ReviewPath
Assert-Contains $Grant14 "Slice 1.15" $Grant14Path

Write-Host "[OK] Official matrix EM-003 status is GROUNDED"
Write-Host "[OK] Slice 1.15 governance event verified"
Write-Host "[OK] Slice 1.15 review verified"
Write-Host "[OK] Slice 1.14 limited authority artifact acknowledges Slice 1.15 path"
Write-Host "PASS: Slice 1.15 EM-003 promotion verified."
exit 0
