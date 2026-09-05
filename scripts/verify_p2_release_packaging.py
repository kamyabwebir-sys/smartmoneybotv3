from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile


SCHEMA = "p2_release_packaging_verification.v1"
EXCLUDED_DIRS = {".git", ".venv", "build", "tests", ".pytest_cache", "release"}
EXCLUDED_NAMES = {".p1-reproduction-path"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(
            part in EXCLUDED_DIRS
            or part.startswith(("dist-p2", ".uv-task-cache", ".pytest"))
            for part in rel.parts
        ):
            continue
        if path.name in EXCLUDED_NAMES or path.name.endswith((".pyc", ".pyo")):
            continue
        if "__pycache__" in rel.parts or any(part.endswith(".egg-info") for part in rel.parts):
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def build_source_bundle(root: Path, output: Path) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    files = source_files(root)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in files:
            rel = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            bundle.writestr(info, path.read_bytes())
    return {"file_count": len(files), "sha256": sha256(output), "path": output.name}


def run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True, env=env)


def verify_build_and_install(root: Path, work: Path) -> dict[str, object]:
    build_dir = work / "build"
    env = dict(os.environ)
    env["UV_CACHE_DIR"] = str(work / "uv-cache")
    run(["uv", "build", "--out-dir", str(build_dir), "--no-sources", str(root)], root, env)
    artifacts = sorted(
        item for item in build_dir.iterdir()
        if item.is_file() and item.name.startswith("smartmoneybotv3-0.1.0")
    )
    wheel = next((item for item in artifacts if item.suffix == ".whl"), None)
    sdist = next((item for item in artifacts if item.name.endswith(".tar.gz")), None)
    if wheel is None or sdist is None:
        raise RuntimeError("wheel and sdist were not produced")
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        if "smartmoneybotv3-0.1.0.dist-info/METADATA" not in names:
            raise RuntimeError("wheel metadata is missing")
        if not any(name.startswith("smart_money/") for name in names):
            raise RuntimeError("wheel smart_money package is missing")
    venv = work / "venv"
    run(["uv", "venv", str(venv), "--python", "3.12"], root, env)
    python = venv / "Scripts" / "python.exe"
    run(["uv", "pip", "install", "--offline", "--no-deps", "--python", str(python), str(wheel)], root, env)
    run([str(python), "-c", "import smart_money; import smart_money.core.ids"], root, env)
    return {
        "wheel": {"name": wheel.name, "sha256": sha256(wheel), "bytes": wheel.stat().st_size},
        "sdist": {"name": sdist.name, "sha256": sha256(sdist), "bytes": sdist.stat().st_size},
        "offline_install": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/release"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True, exist_ok=True)
    first = build_source_bundle(root, args.output / "smartmoneybotv3-source.zip")
    with tempfile.TemporaryDirectory(prefix="p2-packaging-") as temp:
        build = verify_build_and_install(root, Path(temp))
    result = {"source_bundle": first, "build": build, "schema_version": SCHEMA, "status": "PASS"}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
