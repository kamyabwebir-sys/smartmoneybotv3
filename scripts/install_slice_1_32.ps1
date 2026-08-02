#Requires -Version 7.0
<#
Slice 1.32 — Canonical Snapshot and Governance Inventory Lock

Scope:
- Governance/docs-only inventory lock
- Records snapshot ambiguity explicitly
- Creates freeze pack, review stub, receipt, and inventory artifact
- Does not touch source code, tests, protected baseline, execution, risk, or ML logic

Protected files intentionally not modified:
- src/smart_money/discovery/registry.py
- tests/discovery/test_registry.py
#>

[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SliceId = "1.32"
$SliceSlug = "slice_1_32_canonical_snapshot_and_governance_inventory_lock"
$UtcNow = '2026-08-02T20:37:59Z'

function Fail-Closed {
    param([Parameter(Mandatory = $true)][string]$Message)
    Write-Error "FAIL-CLOSED: $Message"
    exit 1
}

function Write-TextFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )

    if ((Test-Path -LiteralPath $Path) -and -not $Force) {
        Fail-Closed "Refusing to overwrite existing file without -Force: $Path"
    }

    $Parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $Parent)) {
        New-Item -ItemType Directory -Path $Parent -Force | Out-Null
    }

    Set-Content -LiteralPath $Path -Value $Content -Encoding UTF8NoBOM
}

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Object
    )

    $Json = $Object | ConvertTo-Json -Depth 20
    Write-TextFile -Path $Path -Content $Json
}

function Assert-RepoRoot {
    param([Parameter(Mandatory = $true)][string]$Root)

    if (-not (Test-Path -LiteralPath $Root)) {
        Fail-Closed "Repo root does not exist: $Root"
    }

    $ExpectedAny = @(
        "pyproject.toml",
        "pytest.ini",
        "README.md",
        "docs",
        "src",
        "tests"
    )

    $Found = @()
    foreach ($Item in $ExpectedAny) {
        $Candidate = Join-Path $Root $Item
        if (Test-Path -LiteralPath $Candidate) {
            $Found += $Item
        }
    }

    if ($Found.Count -lt 2) {
        Fail-Closed "Path does not look like the smartmoneybotv3 repo root: $Root"
    }
}

function Assert-ProtectedFilesUntouchedIntent {
    param([Parameter(Mandatory = $true)][string]$Root)

    $Protected = @(
        "src/smart_money/discovery/registry.py",
        "tests/discovery/test_registry.py"
    )

    foreach ($Rel in $Protected) {
        $Full = Join-Path $Root $Rel
        if (Test-Path -LiteralPath $Full) {
            Write-Host "Protected baseline present and not modified by this installer: $Rel"
        }
    }
}

function Get-InventoryEntry {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$RelativePath,
        [Parameter(Mandatory = $true)][string]$Classification,
        [Parameter(Mandatory = $true)][string]$Notes
    )

    $FullPath = Join-Path $Root $RelativePath
    $Exists = Test-Path -LiteralPath $FullPath

    $Type = "missing"
    if ($Exists) {
        $Item = Get-Item -LiteralPath $FullPath
        if ($Item.PSIsContainer) {
            $Type = "directory"
        } else {
            $Type = "file"
        }
    }

    [ordered]@{
        path = $RelativePath
        exists = $Exists
        type = $Type
        classification = $Classification
        notes = $Notes
    }
}

function Get-FileCount {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$RelativePath
    )

    $FullPath = Join-Path $Root $RelativePath
    if (-not (Test-Path -LiteralPath $FullPath)) {
        return 0
    }

    $Item = Get-Item -LiteralPath $FullPath
    if (-not $Item.PSIsContainer) {
        return 1
    }

    return @(Get-ChildItem -LiteralPath $FullPath -Recurse -File -Force).Count
}

$RepoRoot = (Get-Item -LiteralPath $RepoRoot -ErrorAction Stop).FullName

Assert-RepoRoot -Root $RepoRoot
Assert-ProtectedFilesUntouchedIntent -Root $RepoRoot

$DocsFreezePacksDir = Join-Path $RepoRoot "docs/freeze_packs"
$DocsReviewsDir = Join-Path $RepoRoot "docs/reviews"
$ArtifactsGovernanceDir = Join-Path $RepoRoot "artifacts/governance"

$FreezePackPath = Join-Path $DocsFreezePacksDir "$SliceSlug.md"
$ReviewPath = Join-Path $DocsReviewsDir "$SliceSlug`_review.md"
$InventoryPath = Join-Path $ArtifactsGovernanceDir "$SliceSlug.inventory.json"
$ReceiptPath = Join-Path $ArtifactsGovernanceDir "$SliceSlug.receipt.json"

$InventoryEntries = @(
    Get-InventoryEntry -Root $RepoRoot -RelativePath "pyproject.toml" -Classification "canonical-root-signal" -Notes "Repository root marker when present."
    Get-InventoryEntry -Root $RepoRoot -RelativePath "pytest.ini" -Classification "canonical-root-signal" -Notes "Test configuration root marker when present."
    Get-InventoryEntry -Root $RepoRoot -RelativePath "README.md" -Classification "canonical-root-signal" -Notes "Root documentation marker when present."
    Get-InventoryEntry -Root $RepoRoot -RelativePath "docs" -Classification "governance-docs-root" -Notes "Governance and architecture documentation area."
    Get-InventoryEntry -Root $RepoRoot -RelativePath "docs/freeze_packs" -Classification "freeze-pack-area" -Notes "Expected location for locked slice freeze packs."
    Get-InventoryEntry -Root $RepoRoot -RelativePath "docs/reviews" -Classification "review-area" -Notes "Expected location for review verdict documents."
    Get-InventoryEntry -Root $RepoRoot -RelativePath "docs/governance/receipts" -Classification "legacy-or-parallel-receipt-area" -Notes "Observed receipt location in prior snapshots; inventory only."
    Get-InventoryEntry -Root $RepoRoot -RelativePath "artifacts/governance" -Classification "governance-artifact-area" -Notes "Expected machine-readable governance artifacts."
    Get-InventoryEntry -Root $RepoRoot -RelativePath "scripts" -Classification "installer-verifier-area" -Notes "Expected location for PowerShell installers and verifiers."
    Get-InventoryEntry -Root $RepoRoot -RelativePath "src/smart_money" -Classification "canonical-package-root" -Notes "Canonical-looking package root; read-only for this slice."
    Get-InventoryEntry -Root $RepoRoot -RelativePath "src/smartmoneybot" -Classification "legacy-or-ambiguous-package-root" -Notes "Legacy/ambiguous package root if present; inventory only."
    Get-InventoryEntry -Root $RepoRoot -RelativePath "smartmoneybotv3/src/smartmoneybot" -Classification "nested-snapshot-or-ambiguous-package-root" -Notes "Nested package root observed in some snapshots; inventory only."
    Get-InventoryEntry -Root $RepoRoot -RelativePath "tests" -Classification "test-root" -Notes "Test root; read-only for this slice."
    Get-InventoryEntry -Root $RepoRoot -RelativePath "src/smart_money/discovery/registry.py" -Classification "protected-baseline" -Notes "Protected Slice 0.10 file; must not be modified."
    Get-InventoryEntry -Root $RepoRoot -RelativePath "tests/discovery/test_registry.py" -Classification "protected-baseline" -Notes "Protected Slice 0.10 test; must not be modified."
)

$InventoryObject = [ordered]@{
    slice_id = $SliceId
    slice_name = "Canonical Snapshot and Governance Inventory Lock"
    generated_at_utc = $UtcNow
    status = "inventory-recorded"
    closure_status = "not-claimed"
    promotion_gate = "locked-pending-review"
    deterministic_scope = "governance-docs-only"
    protected_files_not_modified = @(
        "src/smart_money/discovery/registry.py",
        "tests/discovery/test_registry.py"
    )
    guardrails = [ordered]@{
        no_execution_or_trading_logic = $true
        no_risk_calculation = $true
        no_opaque_ml_decisioning = $true
        no_reporting_ui_leakage_into_core_domain = $true
        analytics_does_not_make_direct_decisions = $true
    }
    snapshot_ambiguity = [ordered]@{
        acknowledged = $true
        note = "Multiple prior archives/snapshots may contain root-level and nested project layouts. This inventory records observed paths without promoting ambiguous paths to canonical status."
    }
    counts = [ordered]@{
        docs_files = Get-FileCount -Root $RepoRoot -RelativePath "docs"
        scripts_files = Get-FileCount -Root $RepoRoot -RelativePath "scripts"
        tests_files = Get-FileCount -Root $RepoRoot -RelativePath "tests"
        canonical_package_files = Get-FileCount -Root $RepoRoot -RelativePath "src/smart_money"
        legacy_package_files = Get-FileCount -Root $RepoRoot -RelativePath "src/smartmoneybot"
        nested_legacy_package_files = Get-FileCount -Root $RepoRoot -RelativePath "smartmoneybotv3/src/smartmoneybot"
    }
    inventory = $InventoryEntries
}

$FreezePack = @'
# Slice 1.32 — Canonical Snapshot and Governance Inventory Lock

Status: Frozen for review
Generated At UTC: 2026-08-02T20:37:59Z

## Current Slice Scope

This slice records a canonical governance inventory without changing runtime code, tests, protected discovery registry files, execution logic, risk logic, or ML decisioning.

The purpose is to reduce roadmap ambiguity before additional implementation slices.

## Guardrails

- No execution/trading logic.
- No risk calculation.
- No opaque ML decisioning.
- No reporting/UI leakage into core/domain logic.
- Analytics remains evidence and score-breakdown only.
- Protected Slice 0.10 files are not modified:
  - `src/smart_money/discovery/registry.py`
  - `tests/discovery/test_registry.py`

## Snapshot Ambiguity Handling

Prior snapshots may contain both root-level and nested project layouts. This slice does not promote ambiguous paths to canonical status by presence alone.

Ambiguous or legacy-looking package roots are inventory entries only unless a later reviewed slice explicitly promotes, deprecates, or removes them.

## Machine-Readable Evidence

- `artifacts/governance/$SliceSlug.inventory.json`
- `artifacts/governance/$SliceSlug.receipt.json`

## Closure Claim

This installer does not claim closure.

Expected review status after installation:
```text
Slice 1.32 = INSTALLED_FOR_REVIEW / NOT_CLOSED
'@

$Review = @'
# Slice 1.32 — Canonical Snapshot and Governance Inventory Lock Review

Status: Draft
Generated At UTC: 2026-08-02T20:37:59Z

## Review Verdict

Pending human or verifier review.

text
Slice 1.32 = INSTALLED_FOR_REVIEW / NOT_CLOSED

## Review Checklist

- [ ] Inventory artifact exists.
- [ ] Receipt exists.
- [ ] Freeze pack exists.
- [ ] No source files changed.
- [ ] No tests changed.
- [ ] Protected baseline files were not modified.
- [ ] Snapshot ambiguity is explicitly documented.
- [ ] Receipt does not claim implementation closure.
- [ ] Promotion gate remains locked pending review.

## Protected Baseline

The following files are out of scope and must remain unchanged:

- `src/smart_money/discovery/registry.py`
- `tests/discovery/test_registry.py`
'@

$ReceiptObject = [ordered]@{
slice_id = $SliceId
slice_name = "Canonical Snapshot and Governance Inventory Lock"
generated_at_utc = $UtcNow
installation_status = "completed"
status = "installed_for_review"
closure_status = "not_closed"
promotion_gate = "locked_pending_review"
scope = "governance_docs_inventory_only"
created_files = @(
"docs/freeze_packs/$SliceSlug.md",
"docs/reviews/$SliceSlug`_review.md",
"artifacts/governance/$SliceSlug.inventory.json",
"artifacts/governance/$SliceSlug.receipt.json"
)
modified_source_files = @()
modified_test_files = @()
protected_files_modified = @()
protected_files = @(
"src/smart_money/discovery/registry.py",
"tests/discovery/test_registry.py"
)
guardrails = [ordered]@{
no_execution_or_trading_logic = $true
no_risk_calculation = $true
no_opaque_ml_decisioning = $true
no_reporting_ui_leakage_into_core_domain = $true
analytics_does_not_make_direct_decisions = $true
}
evidence = [ordered]@{
inventory_artifact = "artifacts/governance/$SliceSlug.inventory.json"
freeze_pack = "docs/freeze_packs/$SliceSlug.md"
review = "docs/reviews/$SliceSlug`_review.md"
}
verdict = "INSTALLED_FOR_REVIEW_NOT_CLOSED"
}

Write-JsonFile -Path $InventoryPath -Object $InventoryObject
Write-TextFile -Path $FreezePackPath -Content $FreezePack
Write-TextFile -Path $ReviewPath -Content $Review
Write-JsonFile -Path $ReceiptPath -Object $ReceiptObject

Write-Host ""
Write-Host "Slice 1.32 installer completed."
Write-Host "Status: INSTALLED_FOR_REVIEW / NOT_CLOSED"
Write-Host "Created:"
Write-Host "  - docs/freeze_packs/$SliceSlug.md"
Write-Host "  - docs/reviews/$SliceSlug`_review.md"
Write-Host "  - artifacts/governance/$SliceSlug.inventory.json"
Write-Host "  - artifacts/governance/$SliceSlug.receipt.json"
Write-Host ""
Write-Host "Protected baseline not modified:"
Write-Host "  - src/smart_money/discovery/registry.py"
Write-Host "  - tests/discovery/test_registry.py"

