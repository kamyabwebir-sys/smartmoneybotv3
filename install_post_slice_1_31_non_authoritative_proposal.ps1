Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Root detection aligned with slice 1.30 verifier convention
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Get-Location).Path
}

$ReviewDir = Join-Path $RepoRoot "docs/governance/reviews"
$ProposalPath = Join-Path $ReviewDir "post_slice_1_31_next_scope_grounding_proposal.md"

# Hard guardrails: do not touch protected implementation areas
$ProtectedRoots = @(
    (Join-Path $RepoRoot "src"),
    (Join-Path $RepoRoot "tests")
)

foreach ($protected in $ProtectedRoots) {
    if ($ProposalPath.StartsWith($protected, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "PROTECTED_FILE_MUTATION: proposal path resolved inside protected area: $protected"
    }
}

if (-not (Test-Path -LiteralPath $ReviewDir)) {
    New-Item -ItemType Directory -Force -Path $ReviewDir | Out-Null
}

$Content = @"
# Post-Slice 1.31 Next Scope Grounding Proposal

Status: NON_AUTHORITATIVE_PROPOSAL
Mode: INVENTORY_ONLY
Authority: NONE
Implementation Authority: NOT_GRANTED
Promotion Authority: NOT_GRANTED

## Purpose
This artifact records a non-authoritative grounding proposal for post-slice 1.31 review.
It is documentation-only and exists to support future governance review.

## Constraints
- No implementation authority is granted.
- No promotion authority is granted.
- No execution or trading logic is introduced.
- No risk calculation is introduced.
- No opaque ML decisioning is introduced.
- No mutation of src/** or tests/** is allowed.
- Repository remains in read-only governance posture for post-1.31 scope.

## Notes
Any future work must be separately approved under an explicit slice authority.
This document is a grounding artifact only.
"@

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

if (Test-Path -LiteralPath $ProposalPath) {
    $Existing = [System.IO.File]::ReadAllText($ProposalPath)
    if ($Existing -ceq $Content) {
        Write-Host "IDEMPOTENT_NOOP: canonical proposal already present."
        exit 0
    }

    throw "CANONICAL_HASH_DRIFT: existing proposal content differs from canonical content."
}

[System.IO.File]::WriteAllText($ProposalPath, $Content, $Utf8NoBom)

$Written = [System.IO.File]::ReadAllText($ProposalPath)
if ($Written -cne $Content) {
    throw "CANONICAL_HASH_DRIFT: written proposal does not match canonical content after write."
}

Write-Host "OK: non-authoritative proposal installed at $ProposalPath"
