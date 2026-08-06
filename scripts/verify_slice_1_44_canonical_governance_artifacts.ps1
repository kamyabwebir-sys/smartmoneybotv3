#requires -Version 7.0

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-RepositoryRoot {
    $candidate = $PSScriptRoot

    if ([string]::IsNullOrWhiteSpace($candidate)) {
        $candidate = (Get-Location).Path
    }

    $candidate = (Resolve-Path -LiteralPath $candidate).Path

    try {
        $gitRoot = & git -C $candidate rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($gitRoot)) {
            return (Resolve-Path -LiteralPath ($gitRoot | Select-Object -First 1)).Path
        }
    }
    catch {
        # Deterministic parent traversal fallback.
    }

    $current = Get-Item -LiteralPath $candidate

    while ($null -ne $current) {
        if (Test-Path -LiteralPath (Join-Path $current.FullName '.git')) {
            return $current.FullName
        }

        $current = $current.Parent
    }

    throw 'Repository root could not be resolved.'
}

function Get-Utf8NoBomBytes {
    param([Parameter(Mandatory)][string]$Text)

    $utf8 = [System.Text.UTF8Encoding]::new($false)
    return $utf8.GetBytes($Text)
}

function Get-Sha256Hex {
    param([Parameter(Mandatory)][string]$Text)

    $bytes = Get-Utf8NoBomBytes -Text $Text
    $hash = [System.Security.Cryptography.SHA256]::HashData($bytes)

    return (
        [System.BitConverter]::ToString($hash)
    ).Replace('-', '').ToLowerInvariant()
}

function Assert-File {
    param([Parameter(Mandatory)][string]$RelativePath)

    $path = Join-Path $script:RepoRoot $RelativePath

    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing canonical artifact: $RelativePath"
    }

    return $path
}

function Assert-UniqueCanonicalName {
    param([Parameter(Mandatory)][string]$FileName)

    $matches = @(
        Get-ChildItem -LiteralPath $script:RepoRoot -Recurse -File -Force |
            Where-Object {
                $_.FullName -notmatch '[\\/]\.git[\\/]' -and
                $_.Name -ceq $FileName
            }
    )

    if ($matches.Count -ne 1) {
        $paths = ($matches | ForEach-Object {
            $_.FullName.Substring($script:RepoRoot.Length).TrimStart('\', '/')
        }) -join ', '

        throw "Expected exactly one canonical file named '$FileName'; found $($matches.Count): $paths"
    }
}

function Assert-Contains {
    param(
        [Parameter(Mandatory)][string]$Text,
        [Parameter(Mandatory)][string]$Marker,
        [Parameter(Mandatory)][string]$Source
    )

    if (
        $Text.IndexOf(
            $Marker,
            [System.StringComparison]::OrdinalIgnoreCase
        ) -lt 0
    ) {
        throw "Required marker '$Marker' is missing from $Source"
    }
}

$script:RepoRoot = Resolve-RepositoryRoot

$upstreamFreezePack =
    'docs/freeze_packs/slice_1_43_freeze_pack.md'

$upstreamProposal =
    'docs/proposals/slice_1_43_governance_grounding_proposal.md'

$freezePath = Assert-File -RelativePath $upstreamFreezePack
$proposalPath = Assert-File -RelativePath $upstreamProposal

Assert-UniqueCanonicalName -FileName (
    Split-Path -Leaf $upstreamFreezePack
)

Assert-UniqueCanonicalName -FileName (
    Split-Path -Leaf $upstreamProposal
)

$freezeText = [System.IO.File]::ReadAllText(
    $freezePath,
    [System.Text.UTF8Encoding]::new($false)
)

$proposalText = [System.IO.File]::ReadAllText(
    $proposalPath,
    [System.Text.UTF8Encoding]::new($false)
)

$combined = "$freezeText`n$proposalText"

foreach ($marker in @(
    'Slice 1.43',
    'Implementation Authority',
    'Promotion Authority'
)) {
    Assert-Contains -Text $combined -Marker $marker -Source 'Slice 1.43 artifacts'
}

Assert-Contains -Text $combined -Marker 'NONE' -Source 'Slice 1.43 artifacts'
Assert-Contains -Text $combined -Marker 'LOCKED' -Source 'Slice 1.43 artifacts'

$protectedPaths = @(
    'src',
    'tests',
    'src/smart_money/discovery/registry.py',
    'tests/discovery/test_registry.py'
)

foreach ($protectedPath in $protectedPaths) {
    $diff = & git -C $script:RepoRoot diff --quiet HEAD -- $protectedPath
    if ($LASTEXITCODE -ne 0) {
        throw "Protected path has a diff relative to HEAD: $protectedPath"
    }
}

$receiptRelativePath =
    'artifacts/governance/slice_1_44_canonical_governance_artifacts.receipt.json'

$receiptPath = Assert-File -RelativePath $receiptRelativePath

$receiptText = [System.IO.File]::ReadAllText(
    $receiptPath,
    [System.Text.UTF8Encoding]::new($false)
)

try {
    $receipt = $receiptText | ConvertFrom-Json
}
catch {
    throw "Receipt is not valid JSON: $receiptRelativePath"
}

$expected = [ordered]@{
    schema_version = '1'
    receipt_type = 'canonical_governance_artifact_verification'
    slice = '1.44'
    title = 'Canonical Governance Artifact Verification Closure'
    upstream_slice = '1.43'
    implementation_authority = 'NONE'
    promotion_authority = 'LOCKED'
    verification_result = 'PASS'
    execution_authority = 'NONE'
    trading_authority = 'NONE'
    risk_authority = 'NONE'
    ml_decisioning_authority = 'NONE'
    reporting_authority = 'NONE'
    verified_artifacts = @(
        'docs/freeze_packs/slice_1_43_freeze_pack.md',
        'docs/proposals/slice_1_43_governance_grounding_proposal.md'
    )
}

foreach ($property in $expected.Keys) {
    if (-not ($null -ne $receipt.PSObject.Properties[$property])) {
        throw "Receipt property is missing: $property"
    }

    $actual = $receipt.$property

    if ($actual -is [System.Array]) {
        $actualValue = ($actual -join '|')
        $expectedValue = ($expected[$property] -join '|')

        if ($actualValue -cne $expectedValue) {
            throw "Receipt property mismatch: $property"
        }
    }
    elseif ([string]$actual -cne [string]$expected[$property]) {
        throw "Receipt property mismatch: $property"
    }
}

$receiptJson = $receiptText.Trim()

if (
    $receiptJson.Contains('timestamp') -or
    $receiptJson.Contains('Timestamp') -or
    $receiptJson.Contains('absolute_path') -or
    $receiptJson.Contains('machine_id')
) {
    throw 'Receipt contains environment-dependent fields.'
}

$upstreamFreezeHash = Get-Sha256Hex -Text $freezeText
$upstreamProposalHash = Get-Sha256Hex -Text $proposalText

if ($receipt.upstream_artifact_sha256.freeze_pack -cne $upstreamFreezeHash) {
    throw 'Freeze pack SHA-256 does not match receipt.'
}

if ($receipt.upstream_artifact_sha256.proposal -cne $upstreamProposalHash) {
    throw 'Proposal SHA-256 does not match receipt.'
}

$canonicalReceiptHash = Get-Sha256Hex -Text $receiptJson

Write-Output 'SLICE_1_44_CANONICAL_GOVERNANCE_ARTIFACTS: PASS'
Write-Output "CANONICAL_RECEIPT_SHA256: $canonicalReceiptHash"
exit 0