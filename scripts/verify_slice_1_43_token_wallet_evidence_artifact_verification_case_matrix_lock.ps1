# verify_slice_1_43_token_wallet_evidence_artifact_verification_case_matrix_lock.ps1
$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

function Resolve-RepoRoot {
    $start = Split-Path -Parent $MyInvocation.ScriptName
    if ([string]::IsNullOrWhiteSpace($start)) {
        $start = (Get-Location).Path
    }

    $current = [System.IO.DirectoryInfo]::new($start)
    while ($null -ne $current) {
        $pyproject = Join-Path $current.FullName "pyproject.toml"
        $gitDir = Join-Path $current.FullName ".git"
        if ((Test-Path $pyproject) -or (Test-Path $gitDir)) {
            return $current.FullName
        }
        $current = $current.Parent
    }

    return (Get-Location).Path
}

function Require-Path {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path $Path)) {
        throw "Required path missing: $Path"
    }
}

function Require-Marker {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Marker,
        [Parameter(Mandatory = $true)][string]$Path
    )
    if ($Content -notlike "*$Marker*") {
        throw "Missing marker in ${Path}: ${Marker}"
    }
}

$RepoRoot = Resolve-RepoRoot
Set-Location $RepoRoot

$Slug = "slice_1_43_token_wallet_evidence_artifact_verification_case_matrix_lock"
$FreezePath = Join-Path $RepoRoot "docs/freeze_packs/$Slug.md"
$ReviewPath = Join-Path $RepoRoot "docs/reviews/${Slug}_review.md"
$ReceiptPath = Join-Path $RepoRoot "docs/governance/receipts/${Slug}.json"
$ArtifactPath = Join-Path $RepoRoot "artifacts/governance/${Slug}.receipt.json"

Require-Path $FreezePath
Require-Path $ReviewPath
Require-Path $ReceiptPath
Require-Path $ArtifactPath

$FreezeContent = Get-Content -Raw -Path $FreezePath
$ReviewContent = Get-Content -Raw -Path $ReviewPath

$RequiredMarkers = @(
    "Review Verdict: PASS",
    "Slice Status: LOCKED",
    "Matrix Status: LOCKED",
    "Promotion Gate: LOCKED",
    "Governance Only: YES",
    "Implementation Authority: NO",
    "Runtime Authority: NO",
    "Trading Authority: NO",
    "Risk Authority: NO",
    "ML Decision Authority: NO",
    "TW-EVID-001",
    "TW-EVID-015"
)

foreach ($marker in $RequiredMarkers) {
    Require-Marker -Content $FreezeContent -Marker $marker -Path $FreezePath
    Require-Marker -Content $ReviewContent -Marker $marker -Path $ReviewPath
}

$ProtectedFiles = @(
    "src/smart_money/discovery/registry.py",
    "tests/discovery/test_registry.py"
)

if (Get-Command git -ErrorAction SilentlyContinue) {
    foreach ($protected in $ProtectedFiles) {
        $status = git status --porcelain -- $protected 2>$null
        if (-not [string]::IsNullOrWhiteSpace(($status -join ""))) {
            throw "Protected Slice 0.10 file has local mutation: $protected"
        }
    }
}

$Python = @"
import hashlib
import json
import re
import sys
from pathlib import Path

receipt_path = Path(sys.argv[1])
artifact_path = Path(sys.argv[2])

receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
artifact = json.loads(artifact_path.read_text(encoding="utf-8"))

if receipt != artifact:
    raise SystemExit("receipt and artifact mirror mismatch")

required = [
    "slice_id",
    "slice_name",
    "status",
    "governance_only",
    "implementation_authority",
    "runtime_authority",
    "trading_authority",
    "risk_authority",
    "ml_decision_authority",
    "matrix_case_ids",
    "created_at_utc",
    "locked_at_utc",
    "canonical_payload_sha256",
    "receipt_id",
]

for key in required:
    if key not in receipt:
        raise SystemExit(f"missing receipt key: {key}")

if receipt["slice_id"] != "1.43":
    raise SystemExit("slice_id mismatch")
if receipt["status"] != "LOCKED":
    raise SystemExit("status mismatch")
if receipt["governance_only"] is not True:
    raise SystemExit("governance_only must be true")

for key in [
    "implementation_authority",
    "runtime_authority",
    "trading_authority",
    "risk_authority",
    "ml_decision_authority",
]:
    if receipt[key] != "NO":
        raise SystemExit(f"{key} must be NO")

expected_cases = [f"TW-EVID-{i:03d}" for i in range(1, 16)]
if receipt["matrix_case_ids"] != expected_cases:
    raise SystemExit("matrix_case_ids mismatch")

utc_re = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
for key in ["created_at_utc", "locked_at_utc"]:
    if not isinstance(receipt[key], str) or not utc_re.match(receipt[key]):
        raise SystemExit(f"{key} is not a fixed UTC string")
    if receipt[key] != "2026-08-05T00:00:00Z":
        raise SystemExit(f"{key} must match fixed Slice 1.43 UTC timestamp")

payload = dict(receipt)
payload.pop("receipt_id", None)
payload.pop("canonical_payload_sha256", None)

canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

if receipt["canonical_payload_sha256"] != digest:
    raise SystemExit("canonical_payload_sha256 mismatch")

if receipt["receipt_id"] != "sha256:" + digest:
    raise SystemExit("receipt_id mismatch")

print("PASS slice_1_43 token wallet evidence artifact verification case matrix lock")
"@

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python -c $Python $ReceiptPath $ArtifactPath
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -c $Python $ReceiptPath $ArtifactPath
} else {
    throw "Python is required for canonical JSON SHA-256 verification."
}