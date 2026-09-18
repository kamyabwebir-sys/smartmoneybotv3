$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# ------------------------------------------------------------
# Slice 1.0 Review Verdict Template Installer
# Governance mode:
#   - docs-only
#   - fail-closed
#   - no src/tests changes
# ------------------------------------------------------------

function Assert-GitRepo {
    git rev-parse --show-toplevel *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Not inside a git repository."
    }
}

function Assert-NoRuntimeDiff {
    $srcDiff = git diff --name-only -- src
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to inspect src diff."
    }

    $testDiff = git diff --name-only -- tests
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to inspect tests diff."
    }

    if ($srcDiff -or $testDiff) {
        Write-Host ""
        Write-Host "FAIL-CLOSED: src/ or tests/ has diff. Installer will not proceed." -ForegroundColor Red
        Write-Host ""

        if ($srcDiff) {
            Write-Host "src diff:" -ForegroundColor Yellow
            $srcDiff | ForEach-Object { Write-Host "  $_" }
        }

        if ($testDiff) {
            Write-Host "tests diff:" -ForegroundColor Yellow
            $testDiff | ForEach-Object { Write-Host "  $_" }
        }

        Write-Host ""
        Write-Host "Slice 1.0 governance requires docs-only changes." -ForegroundColor Cyan
        throw "Runtime/test diff detected."
    }
}

function Assert-GovernanceAnchors {
    $freezePack = "slice_1_0_freeze_pack.md"
    $matrix = "slice_1_0_evidence_matrix.md"

    if (-not (Test-Path $freezePack)) {
        throw "Missing required governance source: $freezePack"
    }

    if (-not (Test-Path $matrix)) {
        throw "Missing required governance source: $matrix"
    }

    $freezeText = Get-Content -Raw -Path $freezePack
    $matrixText = Get-Content -Raw -Path $matrix

    if ($freezeText -notmatch "Status:\s*BLOCKED") {
        throw "Governance anchor missing: Status: BLOCKED in $freezePack"
    }

    if ($freezeText -notmatch "Implementation Authority:\s*NONE") {
        throw "Governance anchor missing: Implementation Authority: NONE in $freezePack"
    }

    if ($matrixText -notmatch "Slice Status:\s*BLOCKED") {
        throw "Governance anchor missing: Slice Status: BLOCKED in $matrix"
    }

    if ($matrixText -notmatch "Implementation Authority:\s*NONE") {
        throw "Governance anchor missing: Implementation Authority: NONE in $matrix"
    }

    $matrixLines = Get-Content -LiteralPath $matrix

    $em003Line = $matrixLines | Where-Object { $_ -match '^\|\s*EM-003\s*\|' } | Select-Object -First 1
    if ($null -eq $em003Line) {
        throw "Governance anchor missing: EM-003 row in $matrix"
    }
    if ($em003Line -notmatch '\|\s*MISSING\s*\|') {
        throw "Governance anchor missing: EM-003 MISSING in $matrix"
    }

    $em013Line = $matrixLines | Where-Object { $_ -match '^\|\s*EM-013\s*\|' } | Select-Object -First 1
    if ($null -eq $em013Line) {
        throw "Governance anchor missing: EM-013 row in $matrix"
    }
    if ($em013Line -notmatch '\|\s*MISSING\s*\|') {
        throw "Governance anchor missing: EM-013 MISSING in $matrix"
    }
}

Assert-GitRepo
Assert-NoRuntimeDiff
Assert-GovernanceAnchors

$reviewDir = "docs/reviews"
$templatePath = Join-Path $reviewDir "slice_1_0_review_verdict_template.md"

if (-not (Test-Path $reviewDir)) {
    New-Item -ItemType Directory -Path $reviewDir | Out-Null
}

$templateContent = @"
# Slice 1.0 Review Verdict Template

## Review Identity

- Review ID:
- Reviewer:
- Date:
- Related Freeze Pack: `slice_1_0_freeze_pack.md`
- Related Evidence Matrix: `slice_1_0_evidence_matrix.md`

## Governance Baseline

This review is governed by the current Slice 1.0 constraints.

Authoritative baseline:

- Slice 1.0 status remains `BLOCKED`.
- Implementation Authority remains `NONE`.
- This review does not approve implementation.
- This review does not approve source changes.
- This review does not approve test changes.
- This review does not approve package creation.
- This review does not approve module movement.
- This review does not approve architecture refactor.
- This review does not approve reporting/UI leakage into core/domain logic.
- This review does not approve execution, trading, risk calculation, or opaque ML decisioning.

Evidence anchors:

- `slice_1_0_freeze_pack.md`: line 3 declares `Status: BLOCKED`.
- `slice_1_0_freeze_pack.md`: line 4 declares `Implementation Authority: NONE`.
- `slice_1_0_freeze_pack.md`: lines 11-13 state that source/test/package/module/API/behavior implementation changes are not approved.
- `slice_1_0_evidence_matrix.md`: line 4 declares `Slice Status: BLOCKED`.
- `slice_1_0_evidence_matrix.md`: line 5 declares `Implementation Authority: NONE`.
- `slice_1_0_evidence_matrix.md`: line 49 keeps `EM-003` at `MISSING` .
- `slice_1_0_evidence_matrix.md`: line 63 keeps `EM-013` at `MISSING`.

## Review Scope

Allowed:

- Documentation-only governance review.
- Citation-backed confirmation of existing blocked status.
- Citation-backed confirmation of implementation authority being none.
- Citation-backed confirmation that runtime/test changes are not allowed.
- Recording reviewer verdict without changing implementation authority.

Not allowed:

- Any change under `src/`.
- Any change under `tests/`.
- Any implementation patch.
- Any new runtime behavior.
- Any new test behavior.
- Any silent normalization.
- Any EM-003 promotion.
- Any EM-013 repair.
- Any approval implied from a verifier passing.

## Runtime/Test Diff Check

Reviewer must record the exact result before approving this review artifact.

Commands:
```powershell
git diff -- src
git diff -- tests
git status --short

Expected:

text
No src diff.
No tests diff.
Only docs/reviews governance artifact changes are allowed.

Actual observed result:

text
PASTE ACTUAL OUTPUT HERE

Verdict:

- [ ] PASS: No `src/` diff detected.
- [ ] PASS: No `tests/` diff detected.
- [ ] FAIL: `src/` diff detected.
- [ ] FAIL: `tests/` diff detected.

## Freeze Pack Status Check

Reviewer must confirm:

- [ ] `Slice 1.0` remains `BLOCKED`.
- [ ] `Implementation Authority` remains `NONE`.
- [ ] No source implementation authority is granted.
- [ ] No test implementation authority is granted.
- [ ] No package/module movement authority is granted.

Notes:

text
PASTE REVIEW NOTES HERE

## Evidence Matrix Check

Reviewer must confirm:

- [ ] `EM-003` remains `MISSING`.
- [ ] `EM-003` is not promoted, reclassified, or marked `GROUNDED` without separate approval.
- [ ] `EM-013` remains `MISSING`.
- [ ] `EM-013` is not silently repaired.
- [ ] Duplicate/ambiguous path concerns, if any, are not silently normalized.

Notes:

text
PASTE REVIEW NOTES HERE

## Verdict

Choose exactly one:

- [ ] APPROVED AS DOC-ONLY GOVERNANCE ARTIFACT
- [ ] REJECTED: Runtime/test diff detected
- [ ] REJECTED: Attempts to change Slice 1.0 status
- [ ] REJECTED: Attempts to grant implementation authority
- [ ] REJECTED: Attempts EM-003 promotion without separate approval
- [ ] REJECTED: Attempts EM-013 repair without separate Freeze Pack
- [ ] REJECTED: Other governance violation

Final reviewer statement:

text
This verdict does not approve implementation.
This verdict does not change Slice 1.0 from BLOCKED.
This verdict does not change Implementation Authority from NONE.
This verdict does not authorize src/ or tests/ changes.

Reviewer signature:

text
Name:
Date:
Decision:
"@

Set-Content -Path $templatePath -Value $templateContent -Encoding UTF8

Assert-NoRuntimeDiff

Write-Host ""
Write-Host "PASS: Slice 1.0 review verdict template installed." -ForegroundColor Green
Write-Host "Created/updated: $templatePath"
Write-Host ""
Write-Host "Post-check commands:" -ForegroundColor Cyan
Write-Host "  git diff -- src"
Write-Host "  git diff -- tests"
Write-Host "  git status --short"



