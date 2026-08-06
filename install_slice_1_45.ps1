$ErrorActionPreference = "Stop"

$RepoRoot = (Get-Location).Path
$SliceId = "1.45"

$ReviewDir = Join-Path $RepoRoot "docs/governance/reviews"
$ScriptsDir = Join-Path $RepoRoot "scripts"

$ReviewPath = Join-Path $ReviewDir "slice_1_45_post_1_44_next_scope_grounding_review.md"
$VerifierPath = Join-Path $ScriptsDir "verify_slice_1_45_post_1_44_next_scope_grounding.ps1"

$ProtectedFiles = @(
    (Join-Path $RepoRoot "src/smart_money/discovery/registry.py"),
    (Join-Path $RepoRoot "tests/discovery/test_registry.py")
)

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )
    $dir = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
    }
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

foreach ($file in $ProtectedFiles) {
    if (-not (Test-Path -LiteralPath $file)) {
        throw "Protected file missing: $file"
    }
}

$gitStatusOutput = git status --porcelain -- $ProtectedFiles
if ($gitStatusOutput) {
    throw "Fail-Closed: Protected file mutation detected."
}

$ReviewContent = @'
# Slice 1.45 - Post-1.44 Next-Scope Grounding and Authority Decision

Status: Proposed.
Type: Governance-only.
Verdict: GROUNDING_ONLY_PASS

## Authority

Implementation Authority: NONE
Promotion Authority: LOCKED

## Scope

Slice 1.45 records post-1.44 grounding for next-scope selection and classifies stale untracked governance artifacts without granting cleanup, implementation, promotion, execution, trading, risk, or ML authority.

Protected files: UNCHANGED
src/: UNCHANGED
tests/: UNCHANGED

No execution logic.
No trading logic.
No risk calculation.
No opaque ML decisioning.

## Operating Budget

Governance operating budget: 3 files maximum.
Artifact shape: 1 installer, 1 verifier, 1 review artifact.

## Post-1.44 Repository Grounding

Baseline commit: 4aac266 Add slice 1.44 canonical governance artifact verification

The following pre-existing untracked files are classified for future disposition only. Slice 1.45 does not delete, stage, mutate, promote, or execute them.

| Path | Classification | Disposition |
| --- | --- | --- |
| docs/governance/reviews/post_slice_1_31_proposal_review.md | candidate | retain pending explicit governance cleanup slice |
| docs/proposals/post_slice_1_31_next_scope_grounding_proposal.md | candidate | retain pending explicit governance cleanup slice |
| inspect_slice_1_43_receipt_coverage.ps1 | candidate | superseded-or-obsolete pending explicit verification |
| install_post_slice_1_31_non_authoritative_proposal.ps1 | candidate | non-authoritative proposal installer, no execution authority |
| patch_slice_1_43_receipt_coverage.ps1 | candidate | superseded-or-obsolete pending explicit verification |
| repair_slice_1_43_canonical_case_ids.ps1 | candidate | repair candidate, no current authority |

## Decision

Next Authorized Action: explicit future cleanup/disposition slice only.

Slice 1.45 does not authorize implementation work.
Slice 1.45 does not authorize promotion.
Slice 1.45 does not authorize source or test changes.
Slice 1.45 does not authorize mutation of protected files.
'@

$VerifierContent = @'
param(
    [string]$RepoRoot = "."
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$ReviewPath = Join-Path $RepoRoot "docs/governance/reviews/slice_1_45_post_1_44_next_scope_grounding_review.md"

function Require-Path {
    param([Parameter(Mandatory = $true)][string]$PathValue)
    if (-not (Test-Path -LiteralPath $PathValue)) {
        throw "Missing required path: $PathValue"
    }
}

Require-Path -PathValue $ReviewPath

$review = Get-Content -LiteralPath $ReviewPath -Raw

$requiredReviewTerms = @(
    "Slice 1.45 - Post-1.44 Next-Scope Grounding and Authority Decision",
    "Governance-only",
    "Verdict: GROUNDING_ONLY_PASS",
    "Implementation Authority: NONE",
    "Promotion Authority: LOCKED",
    "Protected files: UNCHANGED",
    "src/: UNCHANGED",
    "tests/: UNCHANGED",
    "No execution logic.",
    "No trading logic.",
    "No risk calculation.",
    "No opaque ML decisioning.",
    "Governance operating budget: 3 files maximum.",
    "Next Authorized Action: explicit future cleanup/disposition slice only.",
    "docs/governance/reviews/post_slice_1_31_proposal_review.md",
    "docs/proposals/post_slice_1_31_next_scope_grounding_proposal.md",
    "inspect_slice_1_43_receipt_coverage.ps1",
    "install_post_slice_1_31_non_authoritative_proposal.ps1",
    "patch_slice_1_43_receipt_coverage.ps1",
    "repair_slice_1_43_canonical_case_ids.ps1"
)

foreach ($term in $requiredReviewTerms) {
    if ($review -notlike "*$term*") {
        throw "Missing required review term: $term"
    }
}

$fenceCount = ([regex]::Matches($review, '
```')).Count
if (($fenceCount % 2) -ne 0) {
throw "Unbalanced markdown code fence in review artifact."
}
$protectedFiles = @(
(Join-Path $RepoRoot "src/smart_money/discovery/registry.py"),
(Join-Path $RepoRoot "tests/discovery/test_registry.py")
)

foreach ($file in $protectedFiles) {
if (-not (Test-Path -LiteralPath $file)) {
throw "Protected file missing: $file"
}
}

$gitStatusOutput = git status --porcelain -- $protectedFiles
if ($gitStatusOutput) {
throw "Fail-Closed: Protected file mutation detected."
}

Write-Host "Slice 1.45 post-1.44 next-scope grounding verification passed."
'@

Write-Utf8NoBom -Path $ReviewPath -Content $ReviewContent
Write-Utf8NoBom -Path $VerifierPath -Content $VerifierContent

& pwsh -NoProfile -File $VerifierPath -RepoRoot $RepoRoot
if ($LASTEXITCODE -ne 0) {
throw "Fail-Closed: Slice 1.45 verifier failed."
}

Write-Host "Slice $SliceId installed."
Write-Host "Review: $ReviewPath"
Write-Host "Verifier: $VerifierPath"
