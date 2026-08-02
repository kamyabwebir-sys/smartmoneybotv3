Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Python = @"
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(r'$Root')

SLUG = "slice_1_34_canonical_snapshot_and_governance_inventory_closure"
FREEZE = ROOT / "docs" / "freeze_packs" / f"{SLUG}.md"
REVIEW = ROOT / "docs" / "governance" / "reviews" / f"{SLUG}_review.md"
RECEIPT = ROOT / "docs" / "governance" / "receipts" / f"{SLUG}_receipt.json"

UPSTREAMS = [
    ROOT / "artifacts" / "governance" / "slice_1_32_canonical_snapshot_and_governance_inventory_lock.inventory.json",
    ROOT / "artifacts" / "governance" / "slice_1_32_canonical_snapshot_and_governance_inventory_lock.receipt.json",
    ROOT / "docs" / "freeze_packs" / "slice_1_32_canonical_snapshot_and_governance_inventory_lock.md",
    ROOT / "docs" / "reviews" / "slice_1_32_canonical_snapshot_and_governance_inventory_lock_review.md",
]

def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")

def reject_float(value):
    if isinstance(value, float):
        fail("float value found in receipt")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                fail("non-string JSON key found")
            reject_float(item)
    if isinstance(value, list):
        for item in value:
            reject_float(item)

for path in [FREEZE, REVIEW, RECEIPT, *UPSTREAMS]:
    if not path.exists():
        fail(f"missing required file: {path.as_posix()}")

freeze_text = FREEZE.read_text(encoding="utf-8")
review_text = REVIEW.read_text(encoding="utf-8")

for token in [
    "Slice 1.34",
    "Governance Status: CLOSED",
    "Review Verdict: PASS",
    "Promotion Gate: LOCKED",
    "Implementation/Promotion Authority: NO",
    "src/smart_money/discovery/registry.py",
    "tests/discovery/test_registry.py",
]:
    if token not in freeze_text:
        fail(f"freeze pack missing token: {token}")

for token in [
    "Review Verdict: PASS",
    "Upstream Slice: 1.32",
    "Governance Status: CLOSED",
    "Promotion Gate: LOCKED",
    "Implementation/Promotion Authority: NO",
    "Scope: governance-only",
]:
    if token not in review_text:
        fail(f"review missing token: {token}")

receipt_raw = RECEIPT.read_text(encoding="utf-8")
receipt = json.loads(receipt_raw)
if not isinstance(receipt, dict):
    fail("receipt top-level JSON must be object")
reject_float(receipt)

expected = {
    "slice_id": "1.34",
    "slice_name": "Canonical Snapshot and Governance Inventory Closure",
    "receipt_type": "canonical_snapshot_and_governance_inventory_closure",
    "timestamp_utc": "2026-08-03T00:00:00Z",
    "review_verdict": "PASS",
    "governance_status": "CLOSED",
    "promotion_gate": "LOCKED",
    "implementation_promotion_authority": "NO",
    "scope": "governance-only",
    "upstream_slice": "1.32",
    "upstream_status_closed": True,
    "functional_promotion_granted": False,
    "protected_files_modified": [],
}
for key, value in expected.items():
    if receipt.get(key) != value:
        fail(f"receipt field mismatch: {key}")

for path in [
    "src/smart_money/discovery/registry.py",
    "tests/discovery/test_registry.py",
]:
    if path not in receipt.get("protected_paths", []):
        fail(f"protected path missing from receipt: {path}")

for term in ["execution", "trading", "risk calculation", "wallet signing", "opaque ml truth"]:
    if term not in receipt.get("forbidden_scope", []):
        fail(f"forbidden scope term missing: {term}")

contract = receipt.get("contract")
if not isinstance(contract, dict) or contract.get("fail_closed") is not True:
    fail("contract.fail_closed must be true")

receipt_id = receipt.get("receipt_id")
if not isinstance(receipt_id, str) or not re.fullmatch(r"[0-9a-f]{64}", receipt_id):
    fail("receipt_id must be lowercase SHA-256 hex")

payload = dict(receipt)
payload.pop("receipt_id")
canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
expected_id = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
if receipt_id != expected_id:
    fail("receipt_id mismatch")

canonical_with_id = json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
if receipt_raw != canonical_with_id:
    fail("receipt JSON is not canonical compact sorted JSON")

print(f"canonical_receipt_id={receipt_id}")
"@

$Encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Python))
python -c "import base64,sys; exec(base64.b64decode(sys.argv[1]).decode('utf-8'))" $Encoded
