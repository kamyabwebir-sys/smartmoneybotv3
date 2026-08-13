# Verify Slice 1.47 Files
$requiredFiles = @(
    "docs/freeze_packs/slice_1_47_first_implementation_candidate_authorization_envelope.md",
    "docs/governance/reviews/slice_1_47_first_implementation_candidate_authorization_envelope_review.md",
    "scripts/verify_slice_1_47_first_implementation_candidate_authorization_envelope.ps1"
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Error "Missing required file: $file"
        exit 1
    }
}

Write-Host "Slice 1.47 Verification Successful"
exit 0
