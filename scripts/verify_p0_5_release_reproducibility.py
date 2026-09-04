from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib
from typing import Any


_SCHEMA_VERSION = "p0_5_release_reproducibility_manifest.v1"
_DEFAULT_MANIFEST = Path(
    "artifacts/governance/p0_5_release_reproducibility_manifest.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _version_tuple(value: str) -> tuple[int, ...]:
    match = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?", value)
    if match is None:
        raise ValueError(f"invalid version: {value}")
    return tuple(int(part or 0) for part in match.groups())


def _dependency_name(requirement: str) -> str:
    match = re.match(r"^[A-Za-z0-9_.-]+", requirement)
    if match is None:
        raise ValueError(f"invalid dependency requirement: {requirement}")
    return match.group(0).lower().replace("_", "-")


def verify(repository_root: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != _SCHEMA_VERSION:
        raise ValueError("unsupported P0.5 manifest schema")

    for relative_path, expectation in manifest["files"].items():
        actual_hash = _sha256(repository_root / relative_path)
        if actual_hash != expectation["sha256"]:
            raise ValueError(f"release input hash mismatch: {relative_path}")

    pyproject_path = repository_root / "pyproject.toml"
    lock_path = repository_root / "uv.lock"
    with pyproject_path.open("rb") as stream:
        pyproject = tomllib.load(stream)
    with lock_path.open("rb") as stream:
        lock = tomllib.load(stream)

    current_python = sys.version_info[:3]
    minimum_python = _version_tuple(manifest["environment"]["python_min"])
    maximum_python = _version_tuple(manifest["environment"]["python_max_exclusive"])
    if not minimum_python <= current_python < maximum_python:
        raise RuntimeError("Python runtime is outside the release compatibility window")

    requires_python = pyproject["project"]["requires-python"]
    if requires_python != ">=3.11":
        raise ValueError("project Python requirement drift detected")

    optional_dependencies = pyproject["project"]["optional-dependencies"]
    locked_packages = {
        package["name"].lower().replace("_", "-") for package in lock["package"]
    }
    for group, expected_names in manifest["expected_optional_dependencies"].items():
        declared_names = {
            _dependency_name(requirement)
            for requirement in optional_dependencies.get(group, ())
        }
        if declared_names != set(expected_names):
            raise ValueError(f"optional dependency drift detected: {group}")
        missing_from_lock = declared_names - locked_packages
        if missing_from_lock:
            raise ValueError(
                f"dependencies missing from lock: {','.join(sorted(missing_from_lock))}"
            )

    uv_version_output = subprocess.run(
        ["uv", "--version"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    uv_version = uv_version_output.split()[1]
    if _version_tuple(uv_version) < _version_tuple(manifest["environment"]["uv_min"]):
        raise RuntimeError("uv runtime is older than the reproducibility minimum")

    environment = dict(os.environ)
    environment["UV_CACHE_DIR"] = str(repository_root / ".uv-task-cache-p05")
    subprocess.run(
        ["uv", "lock", "--check"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )

    return {
        "lock_status": "PASS",
        "python": ".".join(str(part) for part in current_python),
        "schema_version": "p0_5_release_reproducibility_verification.v1",
        "status": "PASS",
        "uv": uv_version,
        "verified_dependency_groups": sorted(
            manifest["expected_optional_dependencies"]
        ),
    }


def main() -> int:
    repository_root = Path(__file__).resolve().parents[1]
    manifest_path = (
        Path(sys.argv[1]).resolve()
        if len(sys.argv) > 1
        else repository_root / _DEFAULT_MANIFEST
    )
    result = verify(repository_root, manifest_path)
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
