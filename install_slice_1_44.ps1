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
        # Fallback below is intentional.
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
    param(
        [Parameter(Mandatory)]
        [string]$Text
    )

    $utf8 = [System.Text.UTF8Encoding]::new($false)
    return $utf8.GetBytes($Text)
}

function Get-Sha256Hex {
    param(
        [Parameter(Mandatory)]
        [string]$Text
    )

    $bytes = Get-Utf8NoBomBytes -Text $Text
    $hash = [System.Security.Cryptography.SHA256]::HashData($bytes)

    return (
        [System.BitConverter]::ToString($hash)
    ).Replace('-', '').ToLowerInvariant()
}

function Write-CanonicalFile {
    param(
        [Parameter(Mandatory)]
        [string]$RelativePath,

        [Parameter(Mandatory)]
        [string]$Content
    )

    $fullPath = Join-Path $script:RepoRoot $RelativePath
    $parent = Split-Path -Parent $fullPath

    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    if (Test-Path -LiteralPath $fullPath) {
        $existing = [System.IO.File]::ReadAllText(
            $fullPath,
            [System.Text.UTF8Encoding]::new($false)
        )

        if ($existing -cne $Content) {
            throw "Refusing to overwrite divergent file: $RelativePath"
        }

        Write-Host "UNCHANGED $RelativePath"
        return
    }

    $utf8 = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($fullPath, $Content, $utf8)

    Write-Host "CREATED  $RelativePath"
}

$script:RepoRoot = Resolve-RepositoryRoot

$freezePackPath =
    'docs/freeze_packs/slice_1_43_freeze_pack.md'

$proposalPath =
    'docs/proposals/slice_1_43_governance_grounding_proposal.md'

$freezePackAbsolute = Join-Path $RepoRoot $freezePackPath
$proposalAbsolute = Join-Path $RepoRoot $proposalPath

if (-not (Test-Path -LiteralPath $freezePackAbsolute)) {
    throw "Required upstream artifact is missing: $freezePackPath"
}

if (-not (Test-Path -LiteralPath $proposalAbsolute)) {
    throw "Required upstream artifact is missing: $proposalPath"
}

$freezePack = [System.IO.File]::ReadAllText(
    $freezePackAbsolute,
    [System.Text.UTF8Encoding]::new($false)
)

$proposal = [System.IO.File]::ReadAllText(
    $proposalAbsolute,
    [System.Text.UTF8Encoding]::new($false)
)

foreach ($requiredMarker in @(
    'Slice 1.43',
    'Implementation Authority',
    'Promotion Authority'
)) {
    if (
        $freezePack.IndexOf($requiredMarker, [System.StringComparison]::OrdinalIgnoreCase) -lt 0 -and
        $proposal.IndexOf($requiredMarker, [System.StringComparison]::OrdinalIgnoreCase) -lt 0
    ) {
        throw "Required upstream marker is missing: $requiredMarker"
    }
}

$freezePackSha256 = Get-Sha256Hex -Text $freezePack
$proposalSha256 = Get-Sha256Hex -Text $proposal

$verifier = @'
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
'@

$freezePack144 = @'
# Slice 1.44 — Canonical Governance Artifact Verification Closure

## Status

- Slice: `1.44`
- Title: Canonical Governance Artifact Verification Closure
- Slice Type: Governance-only
- Verification Mode: Deterministic / replayable / fail-closed
- Implementation Authority: `NONE`
- Promotion Authority: `LOCKED`

## Objective

این Slice فقط صحت حضور و ساختار canonical artifactهای Slice 1.43 را
تأیید می‌کند. هیچ منطق اجرایی، معاملاتی، ریسک، ML، reporting یا runtime
توسط این Slice ایجاد یا تغییر نمی‌کند.

## Canonical Upstream Artifacts

1. `docs/freeze_packs/slice_1_43_freeze_pack.md`
2. `docs/proposals/slice_1_43_governance_grounding_proposal.md`

## Guardrails

- تغییر در `src/` ممنوع است.
- تغییر در `tests/` ممنوع است.
- تغییر در registry ممنوع است.
- Implementation Authority برابر `NONE` باقی می‌ماند.
- Promotion Authority برابر `LOCKED` باقی می‌ماند.
- verifier فقط evidence و verification result تولید می‌کند.
- receipt نباید timestamp، absolute path یا machine-specific value داشته باشد.

## Acceptance

موفقیت Slice منوط به اجرای موفق verifier زیر است:
```powershell
pwsh -NoProfile -File .\scripts\verify_slice_1_44_canonical_governance_artifacts.ps1
'@

$review144 = @'
# Slice 1.44 — Canonical Governance Artifact Verification Closure Review

## Review Verdict

`PASS` مشروط به اجرای موفق verifier canonical مربوط به Slice 1.44.

## Scope

این review فقط artifact verification و governance closure را پوشش می‌دهد.

## Authority

- Implementation Authority: `NONE`
- Promotion Authority: `LOCKED`
- Execution Authority: `NONE`
- Trading Authority: `NONE`
- Risk Authority: `NONE`
- ML Decisioning Authority: `NONE`
- Reporting Authority: `NONE`

## Verified Upstream Scope

- `docs/freeze_packs/slice_1_43_freeze_pack.md`
- `docs/proposals/slice_1_43_governance_grounding_proposal.md`

## Out of Scope

- هرگونه تغییر در `src/`
- هرگونه تغییر در `tests/`
- تغییر registry
- execution یا trading logic
- risk calculation
- opaque ML decisioning
- promotion یا implementation grant

## Closure Rule

این Slice مجوز implementation یا promotion صادر نمی‌کند. نتیجه صرفاً
canonical governance artifact verification closure است.
'@

$receiptBase = [ordered]@{
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
upstream_artifact_sha256 = [ordered]@{
freeze_pack = $freezePackSha256
proposal = $proposalSha256
}
}

$receipt144 = (
$receiptBase |
ConvertTo-Json -Depth 10
) + "`n"

Write-CanonicalFile `
-RelativePath 'scripts/verify_slice_1_44_canonical_governance_artifacts.ps1' `
-Content $verifier

Write-CanonicalFile `
-RelativePath 'docs/freeze_packs/slice_1_44_canonical_governance_artifact_verification_closure.md' `
-Content $freezePack144

Write-CanonicalFile `
-RelativePath 'docs/governance/reviews/slice_1_44_canonical_governance_artifact_verification_closure_review.md' `
-Content $review144

Write-CanonicalFile `
-RelativePath 'artifacts/governance/slice_1_44_canonical_governance_artifacts.receipt.json' `
-Content $receipt144

Write-Host ''
Write-Host 'Slice 1.44 installer completed.'
Write-Host 'Run the verifier with:'
Write-Host 'pwsh -NoProfile -File .\scripts\verify_slice_1_44_canonical_governance_artifacts.ps1'
