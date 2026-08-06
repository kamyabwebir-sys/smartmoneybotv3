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