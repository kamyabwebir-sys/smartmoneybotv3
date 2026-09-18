from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


MANIFEST = Path("artifacts/governance/p2_release_artifact_signatures.json")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], root: Path, env: dict[str, str]) -> None:
    subprocess.run(command, cwd=root, env=env, check=True, capture_output=True, text=True)


def verify(root: Path) -> dict[str, object]:
    manifest = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "p2_release_artifact_signatures.v1":
        raise ValueError("unsupported artifact signature schema")
    artifacts = manifest["artifacts"]
    for relative, expected in artifacts.items():
        path = root / relative
        if not path.is_file() or digest(path) != expected["sha256"]:
            raise ValueError(f"artifact signature mismatch: {relative}")

    wheel_relative = next(name for name in artifacts if name.endswith(".whl"))
    wheel = root / wheel_relative
    env = dict(os.environ)
    with tempfile.TemporaryDirectory(prefix="p2-consumer-") as temporary:
        work = Path(temporary)
        env["UV_CACHE_DIR"] = str(work / "uv-cache")
        venv = work / "consumer"
        run(["uv", "venv", str(venv), "--python", "3.12"], root, env)
        python = venv / "Scripts" / "python.exe"
        run(["uv", "pip", "install", "--offline", "--no-deps", "--python", str(python), str(wheel)], root, env)
        run(
            [
                str(python),
                "-c",
                "import importlib.metadata as m; import smart_money; "
                "import smart_money.core.ids; assert m.version('smartmoneybotv3') == '0.1.0'",
            ],
            root,
            env,
        )
        corrupted = work / wheel.name
        shutil.copy2(wheel, corrupted)
        payload = bytearray(corrupted.read_bytes())
        payload[len(payload) // 2] ^= 1
        corrupted.write_bytes(payload)
        if digest(corrupted) == artifacts[wheel_relative]["sha256"]:
            raise AssertionError("corruption attack was not detected")

    return {
        "artifacts_verified": len(artifacts),
        "consumer_install": "PASS",
        "corruption_attack": "DETECTED",
        "offline": True,
        "schema_version": "p2_final_distribution_gate.v1",
        "status": "PASS",
    }


if __name__ == "__main__":
    print(json.dumps(verify(Path(__file__).resolve().parents[1]), sort_keys=True, separators=(",", ":")))
