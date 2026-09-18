param(
    [string]$ProjectRoot = ".",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$Doc = Join-Path $Root "docs/core_contract_shape_v1.md"
$Notes = Join-Path $Root "docs/slice_0_4_notes.md"

if (-not (Test-Path -LiteralPath $Doc)) { throw "Missing $Doc" }
if (-not (Test-Path -LiteralPath $Notes)) { throw "Missing $Notes" }

Write-Host "Slice 0.4 documentation is present." -ForegroundColor Green