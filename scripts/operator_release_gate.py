"""Fail-closed human release gate with secret scan and SQLite backup/restore drill."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path

SECRET_PATTERNS = (
    re.compile(r"(?i)(private[_-]?key|secret[_-]?key)\s*[:=]\s*['\"][^'\"]{12,}"),
    re.compile(r"https?://[^\s'\"]+(?:api[_-]?key|token|key)=[^\s'\"&]{8,}"),
    re.compile(r"gmgn_[0-9a-f]{24,}"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scan_secrets(root: Path) -> list[str]:
    findings = []
    allowed = {".py", ".toml", ".md", ".json", ".yml", ".yaml", ".ps1", ".html"}
    for base in (root / "src", root / "api", root / "scripts"):
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in allowed or ".bak." in path.name:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if any(pattern.search(text) for pattern in SECRET_PATTERNS):
                findings.append(path.relative_to(root).as_posix())
    return sorted(findings)


def scan_bundle_secrets(bundle: Path) -> list[str]:
    findings = []
    with zipfile.ZipFile(bundle) as archive:
        for name in archive.namelist():
            if name.endswith("/"):
                continue
            text = archive.read(name).decode("utf-8", errors="replace")
            if any(pattern.search(text) for pattern in SECRET_PATTERNS):
                findings.append(name)
    return sorted(findings)


def worktree_is_clean(root: Path) -> bool:
    result = subprocess.run(["git", "status", "--porcelain=v1"], cwd=root, capture_output=True, text=True, check=False)
    return result.returncode == 0 and not result.stdout


def write_receipt(path: Path, receipt: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def backup_restore_verify(source: Path, backup: Path, restored: Path) -> dict:
    backup.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(source) as original, sqlite3.connect(backup) as target:
        original.backup(target)
    with sqlite3.connect(backup) as saved, sqlite3.connect(restored) as target:
        saved.backup(target)
    with sqlite3.connect(source) as original, sqlite3.connect(restored) as recovery:
        if original.execute("PRAGMA quick_check").fetchone()[0] != "ok" or recovery.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise ValueError("backup integrity check failed")
        source_rows = original.execute("SELECT key,body,digest FROM records ORDER BY key").fetchall()
        restored_rows = recovery.execute("SELECT key,body,digest FROM records ORDER BY key").fetchall()
        if source_rows != restored_rows:
            raise ValueError("restored capture differs from source")
    return {"backup_sha256": sha256(backup), "record_count": len(source_rows), "restore_verified": True}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--capture-db", type=Path, required=True)
    parser.add_argument("--packaging-report", type=Path, required=True)
    parser.add_argument("--release-dir", type=Path, required=True)
    parser.add_argument("--operator", required=True)
    parser.add_argument("--approval", required=True)
    args = parser.parse_args()
    if args.approval != "I_APPROVE_READ_ONLY_RELEASE" or not args.operator.strip():
        raise SystemExit("operator approval phrase and identity are required")
    report = json.loads(args.packaging_report.read_text(encoding="utf-8"))
    packaging_passed = report.get("status") in {"PASS", "CLOSED_LOCKED"}
    offline_passed = report.get("build", {}).get("offline_install") == "PASS" or report.get("offline_install", {}).get("status") == "PASS"
    if not packaging_passed or not offline_passed:
        raise SystemExit("reproducible offline packaging has not passed")
    if not worktree_is_clean(args.root):
        raise SystemExit("release requires a clean committed worktree")
    findings = scan_secrets(args.root)
    if findings:
        raise SystemExit("secret scan failed: " + ",".join(findings))
    args.release_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_restore_verify(args.capture_db, args.release_dir / "capture-backup.sqlite3", args.release_dir / "restore-drill.sqlite3")
    configured_path = Path(report["source_bundle"]["path"])
    candidates = (configured_path,) if configured_path.is_absolute() else (
        args.root / configured_path,
        args.packaging_report.parent / configured_path,
    )
    source_bundle = next((path for path in candidates if path.is_file()), candidates[0])
    if not source_bundle.is_file() or sha256(source_bundle) != report["source_bundle"]["sha256"]:
        raise SystemExit("rollback source bundle missing or hash mismatch")
    bundle_findings = scan_bundle_secrets(source_bundle)
    if bundle_findings:
        raise SystemExit("rollback bundle secret scan failed: " + ",".join(bundle_findings))
    receipt = {
        "schema_version": "human_release_gate.v1", "status": "APPROVED_READ_ONLY",
        "operator": args.operator.strip(), "approved_at_utc": datetime.now(UTC).isoformat(),
        "backup": backup, "packaging_report_sha256": sha256(args.packaging_report),
        "rollback_bundle": {"path": source_bundle.name, "sha256": sha256(source_bundle)},
        "secret_scan": {"status": "PASS", "scanned_roots": ["src", "api", "scripts"], "bundle_files_checked": True},
        "authority": "read_only_shadow_release_only",
    }
    write_receipt(args.release_dir / "human-release-receipt.json", receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
