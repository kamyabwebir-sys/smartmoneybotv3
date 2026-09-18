from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as element_tree
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

TEST_PATTERNS = (
    "tests/application/test_dashboard_*.py",
    "tests/adapters/persistence/test_dashboard_*.py",
)

SOURCE_PATTERNS = (
    "src/smart_money/application/dashboard_*.py",
    "src/smart_money/adapters/persistence/dashboard_*.py",
)

REQUIRED_FILES = (
    "pyproject.toml",
    "scripts/dashboard_release_gate.py",
    "scripts/verify_dashboard_runtime.ps1",
    "tests/scripts/test_dashboard_release_gate.py",
    "docs/governance/dashboard_r8_policy.md",
    ".github/workflows/dashboard-verification.yml",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        with os.fdopen(descriptor, "wb") as temporary:
            temporary.write(encoded)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        with os.fdopen(descriptor, "wb") as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def collect_paths(root: Path, patterns: tuple[str, ...]) -> list[Path]:
    collected: set[Path] = set()
    for pattern in patterns:
        collected.update(path for path in root.glob(pattern) if path.is_file())
    return sorted(collected, key=lambda path: relative(root, path))


def git_metadata(root: Path) -> dict[str, Any]:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    status = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if revision.returncode != 0 or status.returncode != 0:
        return {
            "available": False,
            "commit": None,
            "worktree_clean": None,
        }
    return {
        "available": True,
        "commit": revision.stdout.strip(),
        "worktree_clean": status.stdout == "",
    }


def junit_summary(path: Path) -> dict[str, int]:
    """Summarize a pytest JUnit XML report.

    pytest emits a ``<testsuites>`` wrapper whose totals live on the single
    ``<testsuite>`` child, so read the totals from whichever element carries
    them (wrapper first, then child).
    """
    root = element_tree.parse(path).getroot()
    elements: list[element_tree.Element] = [root]
    if root.tag == "testsuites":
        elements.extend(root.findall("testsuite"))
    values: dict[str, int] = {}
    for name in ("tests", "failures", "errors", "skipped"):
        values[name] = 0
        for element in elements:
            raw = element.attrib.get(name)
            if raw is not None:
                values[name] = int(raw)
                break
    return values


def remove_stale_success(receipt: Path, signature: Path) -> None:
    for path in (receipt, signature):
        if path.exists():
            path.unlink()


def failure(
    artifact_dir: Path,
    receipt: Path,
    signature: Path,
    reason: str,
    details: dict[str, Any],
) -> int:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    remove_stale_success(receipt, signature)
    payload = {
        "schema_version": "dashboard-r8-verification-failure-v1",
        "status": "FAILED",
        "reason": reason,
        "details": details,
        "recorded_at_utc": datetime.now(UTC).isoformat(),
    }
    write_json(artifact_dir / "verification-failure.json", payload)
    print(f"DASHBOARD_R8_GATE=FAILED reason={reason}", file=sys.stderr)
    return 1


def sign_receipt(receipt: Path, signature: Path, private_key: Path) -> None:
    if not private_key.is_file():
        raise RuntimeError(f"private signing key does not exist: {private_key}")
    if shutil.which("openssl") is None:
        raise RuntimeError("openssl is required for the R8.8 production signature")

    completed = subprocess.run(
        [
            "openssl",
            "dgst",
            "-sha256",
            "-sign",
            str(private_key),
            "-out",
            str(signature),
            str(receipt),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        signature.unlink(missing_ok=True)
        raise RuntimeError(
            "RSA-SHA256 receipt signing failed: "
            + (completed.stderr.strip() or completed.stdout.strip())
        )


def execute(arguments: argparse.Namespace) -> int:
    root = arguments.root.resolve()
    artifact_dir = (
        arguments.artifact_dir
        if arguments.artifact_dir.is_absolute()
        else root / arguments.artifact_dir
    ).resolve()
    receipt = artifact_dir / "verification-receipt.json"
    signature = artifact_dir / "verification-receipt.sig"

    if not root.is_dir():
        return failure(
            artifact_dir,
            receipt,
            signature,
            "invalid_root",
            {"root": str(root)},
        )

    required_missing = [
        item for item in REQUIRED_FILES if not (root / item).is_file()
    ]
    source_files = collect_paths(root, SOURCE_PATTERNS)
    test_files = collect_paths(root, TEST_PATTERNS)

    preflight_errors: list[str] = []
    if required_missing:
        preflight_errors.append(
            "missing required files: " + ", ".join(sorted(required_missing))
        )
    if not source_files:
        preflight_errors.append("no dashboard source files matched the approved patterns")
    if not test_files:
        preflight_errors.append("no dashboard tests matched the approved patterns")

    git = git_metadata(root)
    if arguments.require_clean_worktree:
        if not git["available"]:
            preflight_errors.append(
                "R8.8 requires a Git worktree, but Git metadata is unavailable"
            )
        elif not git["worktree_clean"]:
            preflight_errors.append(
                "R8.8 requires a clean worktree before evidence is generated"
            )

    private_key = arguments.private_key.resolve() if arguments.private_key else None
    if arguments.require_signature:
        if private_key is None:
            preflight_errors.append(
                "R8.8 requires --private-key for detached RSA-SHA256 signing"
            )
        elif not private_key.is_file():
            preflight_errors.append(
                f"R8.8 private signing key is missing: {private_key}"
            )
        elif shutil.which("openssl") is None:
            preflight_errors.append("R8.8 requires openssl on PATH")

    if preflight_errors:
        return failure(
            artifact_dir,
            receipt,
            signature,
            "preflight_failed",
            {
                "errors": preflight_errors,
                "git": git,
                "source_file_count": len(source_files),
                "test_file_count": len(test_files),
            },
        )

    artifact_dir.mkdir(parents=True, exist_ok=True)
    remove_stale_success(receipt, signature)

    junit_path = artifact_dir / "pytest-junit.xml"
    output_path = artifact_dir / "pytest-output.txt"
    command = [
        sys.executable,
        "-m",
        "pytest",
        "--junitxml",
        str(junit_path),
        "--disable-warnings",
        "--maxfail=1",
        # Keep pytest temp dirs inside the repo: the shared system temp
        # directory is not reliably writable on multi-user Windows hosts.
        "--basetemp",
        str(artifact_dir / "pytest-tmp"),
        *[str(path) for path in test_files],
    ]

    try:
        completed = subprocess.run(
            command,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        output = completed.stdout
        exit_code = completed.returncode
    except OSError as error:
        output = f"Could not start pytest: {error}\n"
        exit_code = 127

    write_bytes(output_path, output.encode("utf-8", errors="replace"))

    summary: dict[str, int] | None = None
    junit_error: str | None = None
    if junit_path.is_file():
        try:
            summary = junit_summary(junit_path)
        except (OSError, ValueError, element_tree.ParseError) as error:
            junit_error = str(error)
    else:
        junit_error = "pytest did not produce the required JUnit XML report"

    file_hashes = {
        relative(root, path): sha256_file(path)
        for path in sorted(
            {*source_files, *test_files, *(root / item for item in REQUIRED_FILES)},
            key=lambda path: relative(root, path),
        )
    }

    manifest = {
        "schema_version": "dashboard-r8-verification-manifest-v1",
        "root_commit": git["commit"],
        "source_patterns": list(SOURCE_PATTERNS),
        "test_patterns": list(TEST_PATTERNS),
        "source_files": [relative(root, path) for path in source_files],
        "test_files": [relative(root, path) for path in test_files],
        "file_hashes": file_hashes,
        "pytest_command": command,
        "pytest_exit_code": exit_code,
        "pytest_output_sha256": sha256_file(output_path),
        "junit_xml_sha256": sha256_file(junit_path) if junit_path.is_file() else None,
        "junit_summary": summary,
    }
    manifest_path = artifact_dir / "verification-manifest.json"
    write_json(manifest_path, manifest)
    manifest_hash = sha256_file(manifest_path)

    verification_errors: list[str] = []
    if exit_code != 0:
        verification_errors.append(f"pytest exit code was {exit_code}, expected 0")
    if junit_error is not None:
        verification_errors.append(f"invalid JUnit evidence: {junit_error}")
    elif summary is not None:
        if summary["tests"] <= 0:
            verification_errors.append("JUnit report contains zero executed tests")
        if summary["failures"] or summary["errors"]:
            verification_errors.append(
                "JUnit report contains failures or errors"
            )
        if summary["skipped"]:
            verification_errors.append(
                "JUnit report contains skipped tests; gate is fail-closed"
            )

    if verification_errors:
        return failure(
            artifact_dir,
            receipt,
            signature,
            "dashboard_tests_failed",
            {
                "errors": verification_errors,
                "manifest_sha256": manifest_hash,
                "pytest_exit_code": exit_code,
                "junit_summary": summary,
            },
        )

    production = arguments.require_signature
    receipt_payload = {
        "schema_version": "dashboard-r8-verification-receipt-v1",
        "scope": "dashboard-r8",
        "gate_status": "R8_8_PRODUCTION_PASSED" if production else "R8_7_VERIFIED",
        "production_authority": "granted" if production else "not_granted",
        "manifest_path": "verification-manifest.json",
        "manifest_sha256": manifest_hash,
        "root_commit": git["commit"],
        "worktree_clean_before_run": git["worktree_clean"],
        "pytest_exit_code": exit_code,
        "junit_summary": summary,
        "signature": (
            {
                "mode": "detached-rsa-sha256",
                "path": "verification-receipt.sig",
            }
            if production
            else {
                "mode": "unsigned",
                "reason": "R8.7 verification is not production authority",
            }
        ),
        "verified_at_utc": datetime.now(UTC).isoformat(),
    }

    try:
        write_json(receipt, receipt_payload)
        if production:
            assert private_key is not None
            sign_receipt(receipt, signature, private_key)
    except (OSError, RuntimeError) as error:
        return failure(
            artifact_dir,
            receipt,
            signature,
            "receipt_or_signature_failed",
            {"error": str(error), "manifest_sha256": manifest_hash},
        )

    print(
        "DASHBOARD_R8_GATE="
        + ("R8_8_PRODUCTION_PASSED" if production else "R8_7_VERIFIED")
    )
    print(f"RECEIPT={receipt}")
    if production:
        print(f"SIGNATURE={signature}")
    return 0


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail-closed R8.7/R8.8 dashboard verification gate."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=Path("artifacts/dashboard/r8"),
    )
    parser.add_argument(
        "--require-clean-worktree",
        action="store_true",
        help="Require a clean Git worktree. Mandatory for R8.8.",
    )
    parser.add_argument(
        "--require-signature",
        action="store_true",
        help="Require detached RSA-SHA256 signing. Mandatory for R8.8.",
    )
    parser.add_argument(
        "--private-key",
        type=Path,
        help="RSA private PEM key used only for the detached R8.8 signature.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(execute(parse_arguments()))