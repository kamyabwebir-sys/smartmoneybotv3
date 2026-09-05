[CmdletBinding()]
param(
    [string]$ManifestPath = "artifacts/governance/p0_4_release_artifact_inventory.json",
    [switch]$SnapshotOnly
)

$ErrorActionPreference = "Stop"
$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ExcludedRelativePaths = @(
    "artifacts/governance/p0_4_release_artifact_inventory.json",
    "artifacts/governance/p0_4_release_artifact_inventory.receipt.json",
    "scripts/verify_p0_4_release_artifact_inventory.ps1",
    "artifacts/governance/p0_5_release_reproducibility_manifest.json",
    "artifacts/governance/p0_5_release_reproducibility.receipt.json",
    "scripts/verify_p0_5_release_reproducibility.py",
    "tests/scripts/test_p0_5_release_reproducibility.py",
    "artifacts/governance/p0_6_release_bundle_manifest.json",
    "artifacts/governance/p0_6_release_bundle_offline_gate.receipt.json",
    "scripts/verify_p0_6_release_bundle_offline.py",
    "tests/scripts/test_p0_6_release_bundle_offline.py",
    "artifacts/governance/p1_clean_machine_reproduction.receipt.json",
    "artifacts/governance/p2_release_packaging_manifest.json",
    "artifacts/governance/p2_1_to_p2_3_release_packaging.receipt.json",
    "artifacts/governance/p2_release_artifact_signatures.json",
    "artifacts/governance/p2_4_to_p2_6_final_distribution.receipt.json",
    "scripts/verify_p2_release_packaging.py",
    "scripts/verify_p2_distribution_gate.py"
)

function Get-TextDigest {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Text)

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    $digest = [System.Security.Cryptography.SHA256]::HashData($bytes)
    return [Convert]::ToHexString($digest).ToLowerInvariant()
}

function Get-PortableFileHash {
    param([Parameter(Mandatory)][System.IO.FileInfo]$File)

    $textExtensions = @(
        ".json", ".lock", ".md", ".ps1", ".py", ".toml", ".txt", ".yaml", ".yml"
    )
    if (
        $File.Extension.ToLowerInvariant() -in $textExtensions -or
        -not $File.Extension -or
        $File.Name -eq ".gitignore"
    ) {
        $text = [System.IO.File]::ReadAllText($File.FullName).Replace("`r`n", "`n")
        return Get-TextDigest -Text $text
    }
    return (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-ScopeSnapshot {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string[]]$Paths
    )

    $records = foreach ($relativeRoot in $Paths) {
        $absoluteRoot = Join-Path $RepositoryRoot $relativeRoot
        if (Test-Path -LiteralPath $absoluteRoot -PathType Leaf) {
            $files = @(Get-Item -LiteralPath $absoluteRoot)
        }
        elseif (Test-Path -LiteralPath $absoluteRoot -PathType Container) {
            $files = @(Get-ChildItem -LiteralPath $absoluteRoot -File -Recurse)
        }
        else {
            throw "inventory scope path is missing: $relativeRoot"
        }

        foreach ($file in $files) {
            $relativePath = [System.IO.Path]::GetRelativePath(
                $RepositoryRoot,
                $file.FullName
            ).Replace("\", "/")
            $excluded = (
                ($relativePath -in $ExcludedRelativePaths) -or
                ($relativePath -match "(^|/)__pycache__/") -or
                ($relativePath -match "(^|/)[^/]+\.egg-info/") -or
                ($relativePath -match "\.py[co]$") -or
                ($relativePath -match "\.bak(\.|$)")
            )
            if ($excluded) {
                continue
            }
            $fileHash = Get-PortableFileHash -File $file
            "$relativePath`t$fileHash"
        }
    }

    $sortedRecords = @($records | Sort-Object -Unique)
    $canonicalText = if ($sortedRecords.Count -eq 0) {
        ""
    }
    else {
        ($sortedRecords -join "`n") + "`n"
    }
    return [ordered]@{
        count = $sortedRecords.Count
        digest = Get-TextDigest -Text $canonicalText
        name = $Name
    }
}

$scopeDefinitions = [ordered]@{
    source = @("src")
    tests = @("tests")
    documentation = @("docs")
    governance = @("artifacts/governance")
    scripts = @("scripts")
    configuration = @(
        "pyproject.toml",
        "uv.lock",
        ".gitignore",
        ".github/workflows/ci.yml"
    )
}

$actualScopes = [ordered]@{}
foreach ($scope in $scopeDefinitions.GetEnumerator()) {
    $actualScopes[$scope.Key] = Get-ScopeSnapshot -Name $scope.Key -Paths $scope.Value
}

if ($SnapshotOnly) {
    [ordered]@{
        schema_version = "p0_4_release_artifact_inventory_snapshot.v1"
        scopes = $actualScopes
    } | ConvertTo-Json -Depth 5
    exit 0
}

$resolvedManifestPath = if ([System.IO.Path]::IsPathRooted($ManifestPath)) {
    $ManifestPath
}
else {
    Join-Path $RepositoryRoot $ManifestPath
}
$manifestFile = Resolve-Path -LiteralPath $resolvedManifestPath
$manifest = Get-Content -Raw -LiteralPath $manifestFile | ConvertFrom-Json
if ($manifest.schema_version -ne "p0_4_release_artifact_inventory.v1") {
    throw "unsupported P0.4 inventory schema"
}

$mismatches = @()
foreach ($scopeName in $scopeDefinitions.Keys) {
    $expected = $manifest.scopes.$scopeName
    $actual = $actualScopes[$scopeName]
    if ($null -eq $expected) {
        $mismatches += "missing_scope:$scopeName"
        continue
    }
    if ([int]$expected.count -ne [int]$actual.count) {
        $mismatches += "count_mismatch:$scopeName"
    }
    if ([string]$expected.digest -ne [string]$actual.digest) {
        $mismatches += "digest_mismatch:$scopeName"
    }
}

if ($mismatches.Count -gt 0) {
    throw "release artifact drift detected: $($mismatches -join ',')"
}

[ordered]@{
    checked_scopes = $scopeDefinitions.Count
    schema_version = "p0_4_release_artifact_inventory_verification.v1"
    status = "PASS"
    total_files = [int](($actualScopes.Values | Measure-Object -Property count -Sum).Sum)
} | ConvertTo-Json -Compress
