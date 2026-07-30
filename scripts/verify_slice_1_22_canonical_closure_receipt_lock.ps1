$ErrorActionPreference = "Stop"

Write-Host "=== Verifying Slice 1.22 Canonical Closure Receipt Lock ===" -ForegroundColor Cyan

$freezePackPath = "docs/freeze_packs/slice_1_22_em_003_canonical_closure_receipt_lock.md"
$reviewPath = "docs/reviews/slice_1_22_em_003_canonical_closure_receipt_lock_review.md"

$requiredFiles = @($freezePackPath, $reviewPath)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path -LiteralPath $file)) {
        throw "Missing required file: $file"
    }
    Write-Host "[OK] Found: $file" -ForegroundColor Green
}

$freeze = Get-Content -LiteralPath $freezePackPath -Raw
$review = Get-Content -LiteralPath $reviewPath -Raw

$requiredFreezeTerms = @(
    '"schema_version": "1"',
    '"receipt_type": "em_003_canonical_closure_receipt"',
    '"slice_id": "1.22"',
    '"governed_slice_id": "1.21"',
    '"governance_verdict": "PASS"',
    '"scope_mode": "governance-only"',
    '"em_003_status_after_closure": "PARTIAL"',
    '"promotion_gate_after_closure": "LOCKED"',
    '"implementation": false',
    '"promotion": false',
    "No wall-clock timestamp",
    "No manual receipt ID injection",
    'Changes to `src/`',
    'Changes to `tests/`'
)

foreach ($term in $requiredFreezeTerms) {
    if (-not $freeze.Contains($term)) {
        throw "Freeze pack missing required term: $term"
    }
    Write-Host "[OK] Freeze term: $term" -ForegroundColor Green
}

$requiredReviewTerms = @(
    "PASS",
    "governance-only",
    "PARTIAL",
    "LOCKED",
    "Authority Granted | NONE",
    "No implementation authority granted",
    "No promotion authority granted"
)

foreach ($term in $requiredReviewTerms) {
    if (-not $review.Contains($term)) {
        throw "Review missing required term: $term"
    }
    Write-Host "[OK] Review term: $term" -ForegroundColor Green
}

$forbiddenTerms = @(
    '"implementation": true',
    '"promotion": true',
    '"em_003_status_after_closure": "GROUNDED"',
    '"promotion_gate_after_closure": "UNLOCKED"',
    "Authority Granted | IMPLEMENTATION",
    "Authority Granted | PROMOTION"
)

foreach ($term in $forbiddenTerms) {
    if ($freeze -like "*$term*" -or $review -like "*$term*") {
        throw "Forbidden term found: $term"
    }
    Write-Host "[OK] Forbidden term absent: $term" -ForegroundColor Green
}

Write-Host "=== Slice 1.22 governance verification PASS ===" -ForegroundColor Cyan
