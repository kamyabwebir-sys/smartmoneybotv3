from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


_SCHEMA_VERSION = "p0_6_release_bundle_manifest.v1"
_DEFAULT_MANIFEST = Path("artifacts/governance/p0_6_release_bundle_manifest.json")


def _sha256(path: Path) -> str:
    content = path.read_bytes()
    if path.suffix.lower() in {".json", ".ps1", ".py"}:
        content = content.replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def verify_bundle_hashes(repository_root: Path, manifest: dict[str, Any]) -> int:
    if manifest.get("schema_version") != _SCHEMA_VERSION:
        raise ValueError("unsupported P0.6 bundle manifest schema")
    checked = 0
    for relative_path, expected_hash in manifest["bundle_inputs"].items():
        path = repository_root / relative_path
        if not path.is_file():
            raise ValueError(f"release bundle input is missing: {relative_path}")
        if _sha256(path) != expected_hash:
            raise ValueError(f"release bundle input hash mismatch: {relative_path}")
        checked += 1
    return checked


def _run_json(command: list[str], repository_root: Path, environment: dict[str, str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"offline verifier produced no receipt: {command[0]}")
    result = json.loads(lines[-1])
    if result.get("status") != "PASS":
        raise RuntimeError(f"offline verifier did not pass: {command[0]}")
    return result


def verify_offline_bundle(
    repository_root: Path,
    manifest_path: Path,
    *,
    full_tests: bool,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checked_inputs = verify_bundle_hashes(repository_root, manifest)

    environment = dict(os.environ)
    environment["UV_OFFLINE"] = "1"
    environment["UV_CACHE_DIR"] = str(repository_root / ".uv-task-cache-p06")

    verification_results = {
        "p0_3": _run_json(
            ["pwsh", "-NoProfile", "-File", "scripts/verify_p0_3_release_baseline_integrity.ps1"],
            repository_root,
            environment,
        ),
        "p0_4": _run_json(
            ["pwsh", "-NoProfile", "-File", "scripts/verify_p0_4_release_artifact_inventory.ps1"],
            repository_root,
            environment,
        ),
        "p0_5": _run_json(
            [sys.executable, "scripts/verify_p0_5_release_reproducibility.py"],
            repository_root,
            environment,
        ),
    }

    test_status = "NOT_REQUESTED"
    if full_tests:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "--basetemp=.pytest-p06-offline",
            ],
            cwd=repository_root,
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        )
        test_status = "PASS"

    return {
        "checked_bundle_inputs": checked_inputs,
        "full_tests": test_status,
        "offline": True,
        "schema_version": "p0_6_release_bundle_offline_verification.v1",
        "status": "PASS",
        "verified_gates": sorted(verification_results),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--full-tests", action="store_true")
    arguments = parser.parse_args()

    repository_root = Path(__file__).resolve().parents[1]
    manifest_path = (
        arguments.manifest.resolve()
        if arguments.manifest is not None
        else repository_root / _DEFAULT_MANIFEST
    )
    result = verify_offline_bundle(
        repository_root,
        manifest_path,
        full_tests=arguments.full_tests,
    )
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
