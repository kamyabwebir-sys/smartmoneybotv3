# scripts/verify_slice_1_48_read_only_consumer_compliance_contract_lock.ps1
$ErrorActionPreference = 'Stop'

function Fail([string]$Message) {
    Write-Host "FAIL: $Message" -ForegroundColor Red
    exit 1
}

$consumerPath = "src/smart_money/discovery/consumer.py"
if (-not (Test-Path $consumerPath)) { Fail "Missing consumer contract file: $consumerPath" }

$content = Get-Content -Path $consumerPath -Raw

if ($content -notmatch "FORBIDDEN_OUTPUT_FIELDS\s*=\s*frozenset\s*\(") {
    Fail "FORBIDDEN_OUTPUT_FIELDS must be defined as frozenset."
}

$requiredFields = @("trade_execution_instruction", "order_intent", "position_sizing")
foreach ($field in $requiredFields) {
    if ($content -notmatch [regex]::Escape($field)) {
        Fail "Missing forbidden output field: $field"
    }
}

Write-Host "PASS: Slice 1.48 read-only consumer compliance contract lock verified." -ForegroundColor Green
