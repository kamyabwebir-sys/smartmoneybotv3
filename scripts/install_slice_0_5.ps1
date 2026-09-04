param(
    [string]$ProjectRoot = ".",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$Doc = Join-Path $Root "docs/serialization_time_id_semantics_v1.md"
$Notes = Join-Path $Root "docs/slice_0_5_notes.md"

if (-not (Test-Path -LiteralPath $Doc)) { throw "Missing $Doc" }
if (-not (Test-Path -LiteralPath $Notes)) { throw "Missing $Notes" }

Write-Host "Slice 0.5 documentation is present." -ForegroundColor Green