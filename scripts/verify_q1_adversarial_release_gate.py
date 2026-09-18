from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)


def main() -> int:
    run([sys.executable, "scripts/verify_q1_security_scans.py"])
    run([sys.executable, "scripts/verify_q1_mutation_smoke.py"])
    run([sys.executable, "-m", "pytest", "-q", "--basetemp=.pytest-q1-gate", "tests/adversarial"])
    run([sys.executable, "scripts/verify_p0_6_release_bundle_offline.py", "--full-tests"])
    print(json.dumps({"slices": ["Q1.7", "Q1.8", "Q1.9", "Q1.10"], "status": "PASS"}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
