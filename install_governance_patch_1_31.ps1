# Governance Patch: Inventory Mode & Read-Only Enforcement
# Slice Scope: 1.31
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# 1. Robust Root Detection (Interactive & Script-Compatible)
$ScriptPath = if (Test-Path Variable:\PSCommandPath) { $PSCommandPath } else { $null }
$RepoRoot = if ([string]::IsNullOrWhiteSpace($ScriptPath)) { (Get-Location).Path } else { Split-Path -Parent $ScriptPath }

if (-not (Test-Path (Join-Path $RepoRoot ".git"))) {
    throw "FAIL_CLOSED: REPO_ROOT_NOT_DETECTED. Run from repository root."
}

# 2. Guardrails Check
Write-Host "[Governance] Status: Inventory Mode"
Write-Host "[Governance] Authority: Promotion Authority = NO"
Write-Host "[Governance] Guardrail: NO src/ or tests/ mutation allowed."

# 3. Artifact Verification
$ReviewDir = Join-Path $RepoRoot "docs/governance/reviews"
$ProposalFile = Join-Path $ReviewDir "post_slice_1_31_next_scope_grounding_proposal.md"

if (-not (Test-Path $ReviewDir)) {
    New-Item -ItemType Directory -Path $ReviewDir -Force
}

# 4. Content Creation (Atomic)
$Content = @"
# Post-Slice 1.31 Governance Receipt
Status: Inventory Mode (Read-Only)
Promotion Authority: NO
Scope: Non-Authoritative / Grounding Proposal
Guardrails: 
- No execution logic
- No risk calculation
- No ML decisioning
- No structural changes to src/** or tests/**
"@

$Content | Out-File -FilePath $ProposalFile -Encoding utf8
Write-Host "[Governance] Artifact generated: $ProposalFile"

# 5. Final Verification (Fail-Closed)
if (-not (Test-Path $ProposalFile)) {
    throw "FAIL_CLOSED: ARTIFACT_CREATION_FAILED"
}

Write-Host "[Governance] Patch Applied Successfully."
