from __future__ import annotations

import ast
from pathlib import Path
import re
import subprocess
import sys
import os


ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|client[_-]?secret|private[_-]?key|access[_-]?token)\s*[:=]\s*['\"][^'\"]{16,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


def scan_secrets() -> int:
    findings = []
    for path in (ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(path.as_posix())
                break
    if findings:
        raise RuntimeError("potential secret material: " + ",".join(findings))
    return 0


def scan_python_ast() -> int:
    for path in (ROOT / "src").rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return 0


def main() -> int:
    scan_secrets()
    scan_python_ast()
    environment = dict(os.environ)
    environment["UV_CACHE_DIR"] = str(ROOT / ".uv-task-cache-q1")
    subprocess.run(
        ["uv", "pip", "check", "--python", sys.executable],
        cwd=ROOT,
        check=True,
        env=environment,
    )
    print('{"dependency_check":"PASS","secret_scan":"PASS","status":"PASS"}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
