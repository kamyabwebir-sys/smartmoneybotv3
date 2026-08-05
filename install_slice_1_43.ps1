# install_slice_1_43.ps1
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

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

function Require-GovernanceMarker {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Marker,
        [Parameter(Mandatory = $true)][string]$Path
    )
    if ($Content -notlike "*$Marker*") {
        throw "Missing governance marker in ${Path}: ${Marker}"
    }
}

$RepoRoot = Resolve-RepoRoot
Set-Location $RepoRoot

$SliceId = "1.43"
$Slug = "slice_1_43_token_wallet_evidence_artifact_verification_case_matrix_lock"
$FixedUtc = "2026-08-05T00:00:00Z"

$FreezeDir = Join-Path $RepoRoot "docs/freeze_packs"
$ReviewDir = Join-Path $RepoRoot "docs/reviews"
$ReceiptDir = Join-Path $RepoRoot "docs/governance/receipts"
$ArtifactDir = Join-Path $RepoRoot "artifacts/governance"
$ScriptsDir = Join-Path $RepoRoot "scripts"

$FreezePath = Join-Path $FreezeDir "$Slug.md"
$ReviewPath = Join-Path $ReviewDir "${Slug}_review.md"
$ReceiptPath = Join-Path $ReceiptDir "${Slug}.json"
$ArtifactPath = Join-Path $ArtifactDir "${Slug}.receipt.json"
$VerifierPath = Join-Path $ScriptsDir "verify_${Slug}.ps1"

@($FreezeDir, $ReviewDir, $ReceiptDir, $ArtifactDir, $ScriptsDir) | ForEach-Object {
    New-Item -ItemType Directory -Force -Path $_ | Out-Null
}

$ProtectedFiles = @(
    "src/smart_money/discovery/registry.py",
    "tests/discovery/test_registry.py"
)

if (Get-Command git -ErrorAction SilentlyContinue) {
    foreach ($protected in $ProtectedFiles) {
        $status = git status --porcelain -- $protected 2>$null
        if (-not [string]::IsNullOrWhiteSpace(($status -join ""))) {
            throw "Protected Slice 0.10 file has local mutation; refusing Slice 1.43 governance install: $protected"
        }
    }
}

$Freeze = @"
# Slice 1.43 - Token and Wallet Evidence Artifact Verification Case Matrix Lock

Slice ID: 1.43
Slice Status: LOCKED
Matrix Status: LOCKED
Review Verdict: PASS
Promotion Gate: LOCKED
Governance Only: YES
Implementation Authority: NO
Runtime Authority: NO
Trading Authority: NO
Risk Authority: NO
ML Decision Authority: NO
Reporting Authority: NO

## Scope

This slice locks the deterministic verifier case matrix for token and wallet evidence artifacts.

It is a governance-only contract lock. It does not authorize runtime implementation, trading logic, execution logic, risk calculation, opaque ML decisioning, alert generation, reporting/UI behavior, or mutation of protected discovery registry files.

## Protected Files

The following files remain protected and must not be changed by this slice:

- src/smart_money/discovery/registry.py
- tests/discovery/test_registry.py

## Verifier Case Matrix

| Case ID | Verification Case | Expected Result |
|---|---|---|
| TW-EVID-001 | Artifact file exists at the declared path. | PASS when present; FAIL when missing. |
| TW-EVID-002 | Artifact is valid JSON and parseable with deterministic tooling. | PASS when valid JSON; FAIL on parse error. |
| TW-EVID-003 | Artifact declares schema_version as a fixed string. | PASS when present and fixed; FAIL when missing or dynamic. |
| TW-EVID-004 | Artifact declares evidence_kind as token_wallet_evidence. | PASS when exact; FAIL otherwise. |
| TW-EVID-005 | Artifact declares token evidence section without runtime enrichment. | PASS when structural only; FAIL on execution-derived enrichment. |
| TW-EVID-006 | Artifact declares wallet evidence section without runtime enrichment. | PASS when structural only; FAIL on execution-derived enrichment. |
| TW-EVID-007 | Token identifiers are canonical strings. | PASS when deterministic strings; FAIL on ambiguous identifiers. |
| TW-EVID-008 | Wallet identifiers are canonical strings. | PASS when deterministic strings; FAIL on ambiguous identifiers. |
| TW-EVID-009 | Evidence timestamps, when present, are fixed UTC strings. | PASS when fixed UTC; FAIL when generated dynamically. |
| TW-EVID-010 | Evidence source references are explicit and replayable. | PASS when source references are stable; FAIL when opaque. |
| TW-EVID-011 | No trading, execution, or order intent fields are introduced. | PASS when absent; FAIL when present. |
| TW-EVID-012 | No risk scoring, exposure sizing, or portfolio action fields are introduced. | PASS when absent; FAIL when present. |
| TW-EVID-013 | No opaque ML decision output is introduced. | PASS when absent; FAIL when present. |
| TW-EVID-014 | Evidence score breakdown, if later authorized, remains explanatory only. | PASS when non-decisional; FAIL when used as decision authority. |
| TW-EVID-015 | Verification result is deterministic and replayable from the artifact bytes. | PASS when replayable; FAIL when dependent on runtime state. |

## Receipt Rules

- receipt_id must be derived from canonical JSON using SHA-256.
- canonical_payload_sha256 must match the canonical payload with receipt_id and canonical_payload_sha256 excluded.
- Temporal fields must be fixed UTC strings.
- Verifier must fail closed on missing markers, missing files, protected-file mutation, or hash mismatch.

## Authority Boundary

Analytics may only produce evidence and score breakdown in future authorized slices. This slice grants no authority for direct decisions.
"@

$Review = @"
# Slice 1.43 Review - Token and Wallet Evidence Artifact Verification Case Matrix Lock

Review Verdict: PASS
Slice Status: LOCKED
Matrix Status: LOCKED
Promotion Gate: LOCKED
Governance Only: YES
Implementation Authority: NO
Runtime Authority: NO
Trading Authority: NO
Risk Authority: NO
ML Decision Authority: NO
Reporting Authority: NO

## Review Summary

Slice 1.43 locks the Token and Wallet Evidence Artifact Verification Case Matrix with cases TW-EVID-001 through TW-EVID-015.

The slice is limited to governance documentation, deterministic receipt capture, and fail-closed verifier generation. It grants no implementation or runtime authority.

## Case Coverage

- TW-EVID-001: LOCKED
- TW-EVID-002: LOCKED
- TW-EVID-003: LOCKED
- TW-EVID-004: LOCKED
- TW-EVID-005: LOCKED
- TW-EVID-006: LOCKED
- TW-EVID-007: LOCKED
- TW-EVID-008: LOCKED
- TW-EVID-009: LOCKED
- TW-EVID-010: LOCKED
- TW-EVID-011: LOCKED
- TW-EVID-012: LOCKED
- TW-EVID-013: LOCKED
- TW-EVID-014: LOCKED
- TW-EVID-015: LOCKED

## Guardrail Review

No execution/trading logic is authorized.
No risk calculation is authorized.
No opaque ML decisioning is authorized.
No reporting/UI leakage into core/domain logic is authorized.
No protected registry file mutation is authorized.

## Closure

Slice 1.43 is approved only as a governance-only contract lock.
"@

$Verifier = @'
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
'@

Write-Utf8NoBom -Path $FreezePath -Content $Freeze
Write-Utf8NoBom -Path $ReviewPath -Content $Review
Write-Utf8NoBom -Path $VerifierPath -Content $Verifier

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
    Require-GovernanceMarker -Content $FreezeContent -Marker $marker -Path $FreezePath
    Require-GovernanceMarker -Content $ReviewContent -Marker $marker -Path $ReviewPath
}

$ReceiptPython = @"
import hashlib
import json
import sys
from pathlib import Path

receipt_path = Path(sys.argv[1])
artifact_path = Path(sys.argv[2])

payload = {
    "slice_id": "1.43",
    "slice_name": "Token and Wallet Evidence Artifact Verification Case Matrix Lock",
    "status": "LOCKED",
    "governance_only": True,
    "implementation_authority": "NO",
    "runtime_authority": "NO",
    "trading_authority": "NO",
    "risk_authority": "NO",
    "ml_decision_authority": "NO",
    "reporting_authority": "NO",
    "protected_files": [
        "src/smart_money/discovery/registry.py",
        "tests/discovery/test_registry.py",
    ],
    "matrix_case_ids": [f"TW-EVID-{i:03d}" for i in range(1, 16)],
    "created_at_utc": "2026-08-05T00:00:00Z",
    "locked_at_utc": "2026-08-05T00:00:00Z",
}

canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

receipt = dict(payload)
receipt["canonical_payload_sha256"] = digest
receipt["receipt_id"] = "sha256:" + digest

text = json.dumps(receipt, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
receipt_path.write_text(text, encoding="utf-8")
artifact_path.write_text(text, encoding="utf-8")
"@

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python -c $ReceiptPython $ReceiptPath $ArtifactPath
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -c $ReceiptPython $ReceiptPath $ArtifactPath
} else {
    throw "Python is required to generate deterministic canonical receipt."
}

& $VerifierPath

Write-Host "PASS Slice 1.43 installed and verified."
Write-Host "Freeze:  $FreezePath"
Write-Host "Review:  $ReviewPath"
Write-Host "Receipt: $ReceiptPath"
Write-Host "Mirror:  $ArtifactPath"
Write-Host "Verify:  $VerifierPath"
