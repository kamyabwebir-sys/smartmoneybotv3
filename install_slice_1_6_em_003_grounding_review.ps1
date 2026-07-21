[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$ExpectedReviewPath = "docs/reviews/slice_1_6_em_003_grounding_review.md"
$InstallerPath = "install_slice_1_6_em_003_grounding_review.ps1"

function Normalize-PathForGit {
    param([string]$Path)
    return $Path.Replace("\", "/")
}

function Assert-InRepoRoot {
    if (-not (Test-Path ".git")) {
        throw "Blocked: this script must be run from the repository root containing .git"
    }
}

function Assert-NoForbiddenPendingChanges {
    $statusLines = git status --porcelain
    $forbidden = @()

    foreach ($line in $statusLines) {
        if ($line.Length -lt 4) {
            continue
        }

        $path = $line.Substring(3).Trim()
        $path = Normalize-PathForGit $path

        if (
            $path -like "src/*" -or
            $path -like "tests/*" -or
            $path -eq "pyproject.toml" -or
            $path -eq "pytest.ini"
        ) {
            $forbidden += $path
        }
    }

    if ($forbidden.Count -gt 0) {
        throw ("Blocked: forbidden pending changes detected:`n - " + ($forbidden -join "`n - "))
    }
}

function Write-ReviewFile {
    $reviewDir = Split-Path $ExpectedReviewPath -Parent

    if (-not (Test-Path $reviewDir)) {
        New-Item -Path $reviewDir -ItemType Directory -Force | Out-Null
    }

    $content = @"
# Slice 1.6 EM-003 Grounding Review

## Document Status
- Type: Documentation-only governance review
- Scope: EM-003 grounding assessment only
- Implementation Authority: NONE
- Approval Status: NOT_APPROVED
- Source/Test Changes Authorized: NO

## Purpose
This review records the current grounding state of EM-003 and prepares exact evidence references needed for any future status update in the Evidence Matrix.

This document does not approve implementation, does not approve source changes, does not approve test changes, and does not change any authoritative governance status by itself.

## Authoritative Governance Baseline
The current governance baseline remains unchanged:

- Slice Status: BLOCKED
- Implementation Authority: NONE
- Approval Status: NOT_APPROVED
- Source/Test Changes Authorized: NO

This review must be interpreted under the existing blocked governance state until a separate authoritative approval explicitly changes that state.

## EM-003 Current Matrix State
Current EM-003 status in the authoritative evidence set:

- Status: PARTIAL
- Interpretation: Some deterministic/replayable evidence exists, but exact references are still required for full grounding.
- Constraint: Contract approval remains blocked if EM-003 is not fully grounded.

## Review Objective
This review has four narrow goals:

1. Restate the exact governance meaning of EM-003.
2. Record candidate authoritative evidence locations relevant to deterministic and replayable behavior.
3. Prevent premature status escalation from PARTIAL to GROUNDED.
4. Define the minimum evidence closure condition for a later matrix update.

## EM-003 Evidence Requirement
EM-003 requires exact grounding for deterministic and replayable system behavior.

For governance purposes, grounded means the evidence must be specific enough to support direct review, not broad enough to rely on interpretation alone.

The future grounding package must show, at minimum:

- deterministic assumptions are explicitly documented
- replayability expectations are explicitly documented
- the documented assumptions align with current authoritative contracts or tests
- no contradictory evidence exists in the current authoritative baseline

## Candidate Evidence Sources
The following files are candidate sources for future exact citation extraction:

- docs/deterministic_assumptions_v1.md
- docs/core_contract_semantics_v1.md
- docs/core_contract_shape_v1.md
- docs/serialization_time_id_semantics_v1.md
- src/smart_money/core/contracts.py
- src/smart_money/core/replay.py
- src/smart_money/core/serialization.py
- src/smart_money/core/time.py
- src/smart_money/core/ids.py
- tests/core/test_golden_replay.py
- tests/test_canonical_serialization.py
- tests/test_deterministic_ids.py
- tests/test_replay_manifest.py

## Review Constraints
This review is intentionally non-authoritative with respect to final EM-003 closure.

This document does not:

- mark EM-003 as GROUNDED
- modify the authoritative Evidence Matrix
- authorize source code changes
- authorize test changes
- change Slice Status from BLOCKED
- grant Implementation Authority

## Evidence Closure Standard
A later Evidence Matrix update may be considered only if all of the following are satisfied:

1. Exact file-level references are collected.
2. Exact line-level references are collected where feasible.
3. The references demonstrate deterministic assumptions explicitly.
4. The references demonstrate replayability expectations explicitly.
5. The references are consistent with current authoritative tests and contracts.
6. A separate governance review confirms that the remaining gap is closed.

## Interim Governance Position
Current recommendation:

- Retain EM-003 as PARTIAL
- Do not update EM-003 to GROUNDED in the Evidence Matrix at this stage
- Continue with exact citation extraction in a follow-up documentation-only step

## Exit Criteria for a Future Update
A future review may recommend PARTIAL -> GROUNDED only if:

- deterministic evidence is exact and reviewable
- replayable evidence is exact and reviewable
- authoritative references are citation-ready
- no unresolved contradiction remains in the baseline
- reviewer sign-off is explicitly recorded

## Final Status
- Review Outcome: OPEN
- Governance Recommendation: RETAIN PARTIAL
- Slice Status Impact: NONE
- Implementation Authority Granted: NONE
"@

    Set-Content -Path $ExpectedReviewPath -Value $content -Encoding UTF8
}

Write-Host "Slice 1.6 EM-003 grounding review installer" -ForegroundColor Cyan

Assert-InRepoRoot
Assert-NoForbiddenPendingChanges
Write-ReviewFile

Write-Host ""
Write-Host "Created/updated expected review file:" -ForegroundColor Green
Write-Host " - $ExpectedReviewPath" -ForegroundColor Green

Write-Host ""
Write-Host "Governance verification passed:" -ForegroundColor Green
Write-Host " - No src/ changes detected" -ForegroundColor Green
Write-Host " - No tests/ changes detected" -ForegroundColor Green
Write-Host " - No pyproject.toml change detected" -ForegroundColor Green
Write-Host " - No pytest.ini change detected" -ForegroundColor Green

Write-Host ""
Write-Host "Next commands:" -ForegroundColor Cyan
Write-Host "git add $ExpectedReviewPath $InstallerPath"
Write-Host 'git commit -m "docs: add slice 1.6 EM-003 grounding review"'
