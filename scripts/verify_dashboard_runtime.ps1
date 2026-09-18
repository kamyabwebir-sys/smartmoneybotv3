[CmdletBinding()]
param(
    [Parameter()]
    [string]$Root = (Get-Location).Path,

    [Parameter()]
    [switch]$Production,

    [Parameter()]
    [string]$PrivateKey
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ResolvedRoot = (Resolve-Path $Root).Path
$Gate = Join-Path $ResolvedRoot "scripts/dashboard_release_gate.py"
if (-not (Test-Path $Gate)) {
    throw "Missing dashboard gate: $Gate"
}

$Arguments = @(
    $Gate,
    "--root", $ResolvedRoot
)

if ($Production) {
    if ([string]::IsNullOrWhiteSpace($PrivateKey)) {
        throw "R8.8 production mode requires -PrivateKey <RSA private PEM path>."
    }

    $Arguments += @(
        "--require-clean-worktree",
        "--require-signature",
        "--private-key", $PrivateKey
    )
}

& python @Arguments
exit $LASTEXITCODE