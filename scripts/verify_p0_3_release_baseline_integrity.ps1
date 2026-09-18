[CmdletBinding()]
param(
    [string]$ManifestPath = "artifacts/governance/p0_3_release_baseline_integrity_manifest.json"
)

$ErrorActionPreference = "Stop"

function Invoke-Git {
    param([Parameter(Mandatory)][string[]]$Arguments)

    $output = & git @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Arguments -join ' ') failed: $output"
    }
    return ($output | Out-String).Trim()
}

$manifestFile = Resolve-Path -LiteralPath $ManifestPath
$manifest = Get-Content -Raw -LiteralPath $manifestFile | ConvertFrom-Json

if ($manifest.schema_version -ne "p0_3_release_baseline_integrity_manifest.v1") {
    throw "unsupported P0.3 manifest schema"
}

$baselineCommit = [string]$manifest.baseline_commit
$actualCommit = Invoke-Git -Arguments @("rev-parse", $baselineCommit)
if ($actualCommit -ne $baselineCommit) {
    throw "baseline commit mismatch"
}

$actualTree = Invoke-Git -Arguments @("rev-parse", "$baselineCommit`^{tree}")
if ($actualTree -ne [string]$manifest.baseline_tree) {
    throw "baseline tree mismatch"
}

& git merge-base --is-ancestor $baselineCommit HEAD
if ($LASTEXITCODE -ne 0) {
    throw "baseline commit is not an ancestor of HEAD"
}

foreach ($property in $manifest.files.PSObject.Properties) {
    $path = $property.Name
    $expectedBlob = [string]$property.Value
    $actualBlob = Invoke-Git -Arguments @("rev-parse", "$baselineCommit`:$path")
    if ($actualBlob -ne $expectedBlob) {
        throw "baseline blob mismatch: $path"
    }
}

$result = [ordered]@{
    baseline_commit = $baselineCommit
    baseline_tree = $actualTree
    checked_files = @($manifest.files.PSObject.Properties).Count
    schema_version = "p0_3_release_baseline_integrity_verification.v1"
    status = "PASS"
}

$result | ConvertTo-Json -Compress
