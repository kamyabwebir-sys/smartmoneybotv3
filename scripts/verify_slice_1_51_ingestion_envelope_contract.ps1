$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $RepoRoot
try {
    python -m pytest `
        tests/ingestion/test_envelope_contract.py `
        tests/ingestion/test_provider_scaffold.py `
        tests/ingestion/test_structure_event_contract.py `
        tests/test_contract_structure_event.py
} finally {
    Pop-Location
}