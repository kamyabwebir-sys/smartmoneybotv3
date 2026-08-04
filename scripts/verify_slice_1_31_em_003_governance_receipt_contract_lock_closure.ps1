Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = $PWD
$ReceiptPath = Join-Path $RepoRoot "docs/governance/receipts/slice_1_31_em_003_governance_receipt_contract_lock_closure.json"

if (-not (Test-Path $ReceiptPath)) {
    Write-Error "Receipt file not found at $ReceiptPath"
    exit 1
}

$json = Get-Content -Path $ReceiptPath -Raw | ConvertFrom-Json

# Canonicalization check
$payload = [ordered]@{
    em_003_status = $json.em_003_status
    execution_authority = $json.execution_authority
    implementation_promotion_authority = $json.implementation_promotion_authority
    ml_decisioning_authority = $json.ml_decisioning_authority
    promotion_gate = $json.promotion_gate
    receipt_id = $json.receipt_id
    receipt_type = $json.receipt_type
    review_verdict = $json.review_verdict
    risk_authority = $json.risk_authority
    scope = $json.scope
    slice = $json.slice
    timestamp = $json.timestamp
    trading_authority = $json.trading_authority
    upstream_slice = $json.upstream_slice
    upstream_verification = $json.upstream_verification
}

# Re-hash check (excluding receipt_id itself from the hashing input as per canonical rules)
$hashPayload = [ordered]@{
    em_003_status = $json.em_003_status
    execution_authority = $json.execution_authority
    implementation_promotion_authority = $json.implementation_promotion_authority
    ml_decisioning_authority = $json.ml_decisioning_authority
    promotion_gate = $json.promotion_gate
    receipt_type = $json.receipt_type
    review_verdict = $json.review_verdict
    risk_authority = $json.risk_authority
    scope = $json.scope
    slice = $json.slice
    timestamp = $json.timestamp
    trading_authority = $json.trading_authority
    upstream_slice = $json.upstream_slice
    upstream_verification = $json.upstream_verification
}

$canonical = $hashPayload | ConvertTo-Json -Compress
$bytes = [System.Text.Encoding]::UTF8.GetBytes($canonical)
$sha = [System.Security.Cryptography.SHA256]::Create()
$hashBytes = $sha.ComputeHash($bytes)
$sha.Dispose()
$expectedId = -join ($hashBytes | ForEach-Object { $_.ToString("x2") })

if ($json.receipt_id -ne $expectedId) {
    Write-Error "Receipt ID mismatch! Expected $expectedId, got $($json.receipt_id)"
    exit 1
}

Write-Host "Slice 1.31 verification passed."
