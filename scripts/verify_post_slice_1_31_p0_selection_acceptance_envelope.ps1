$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = (Get-Location).Path
$ProposalPath = Join-Path $RepoRoot "docs/governance/proposals/post_slice_1_31_next_p0_selection_acceptance_envelope.md"

if (-not (Test-Path $ProposalPath)) {
    throw "Fail-Closed: Proposal file missing."
}

$content = Get-Content -Path $ProposalPath -Raw

$RequiredTokens = @(
    'AnalysisRequest'
    'InputBundleManifest'
    '## 14. Governance Verdict'
    'Verdict: Accepted as proposal envelope for post-slice-1.31 P0 selection.'
    '## 16. Final Constraint Summary'
)

$missing = New-Object System.Collections.Generic.List[string]

foreach ($token in $RequiredTokens) {
    if ($content.IndexOf($token, [System.StringComparison]::Ordinal) -lt 0) {
        $missing.Add($token)
    }
}

if ($missing.Count -gt 0) {
    $message = [string]::Join("; ", $missing)
    throw "Fail-Closed: Proposal verification failed. Missing required content: $message"
}

Write-Host "PASS: post_slice_1_31_next_p0_selection_acceptance_envelope verified."
