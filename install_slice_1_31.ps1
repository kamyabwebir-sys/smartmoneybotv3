Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = $PWD
$ReceiptPath = Join-Path $RepoRoot "docs/governance/receipts/slice_1_31_em_003_governance_receipt_contract_lock_closure.json"

$PythonBuildReceipt = @"
import hashlib
import json
from pathlib import Path

payload = {
    "scope": "governance-only",
    "slice": "1.31",
    "upstream_slice": "1.30",
    "review_verdict": "PASS",
    "em_003_status": "CONTRACT_LOCKED",
    "promotion_gate": "LOCKED",
    "execution_authority": "NO",
    "implementation_promotion_authority": "NO",
    "trading_authority": "NO",
    "risk_authority": "NO",
    "ml_decisioning_authority": "NO",
    "receipt_type": "em_003_governance_receipt_contract_lock_closure",
    "timestamp": "2026-08-01T00:00:00Z",
    "upstream_verification": "Slice 1.30 EM-003 governance receipt contract lock verification passed."
}

canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
receipt_id = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
payload["receipt_id"] = receipt_id

# Use raw string for Windows paths to avoid unicodeescape
output_path = Path(r"""$ReceiptPath""")
output_path.parent.mkdir(parents=True, exist_ok=True)

with output_path.open("w", encoding="utf-8", newline="\n") as handle:
    json.dump(payload, handle, indent=2, ensure_ascii=True)
    handle.write("\n")

print(f"Generated receipt_id: {receipt_id}")
"@

$TmpPy = Join-Path $RepoRoot ".slice_1_31_build_receipt_tmp.py"
$PythonBuildReceipt | Set-Content -Path $TmpPy -Encoding UTF8

try {
    python $TmpPy
    if ($LASTEXITCODE -ne 0) {
        throw "Python script failed with exit code $LASTEXITCODE"
    }
}
finally {
    if (Test-Path $TmpPy) { Remove-Item $TmpPy -Force }
}

Write-Host "Slice 1.31 installer completed successfully."
