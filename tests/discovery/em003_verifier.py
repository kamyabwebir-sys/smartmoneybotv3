from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_evidence_report() -> dict[str, Any]:
    return {
        "em_id": "EM-003",
        "status": "PARTIAL",
        "approval_status": "NOT_APPROVED",
        "promotion_gate": "LOCKED",
        "implementation_authority": "NONE",
        "deterministic": True,
        "replayable": True,
        "cases": [
            {"id": f"EM003-CASE-{i:03d}", "status": "NOT_EXECUTED"}
            for i in range(1, 11)
        ],
    }


def build_attachment_register() -> dict[str, Any]:
    return {
        "em_id": "EM-003",
        "artifacts": [
            "artifacts/discovery/em003/evidence_report.json",
            "artifacts/discovery/em003/attachment_register.json",
        ],
    }


def write_artifacts(root: Path) -> None:
    out_dir = root / "artifacts" / "discovery" / "em003"
    out_dir.mkdir(parents=True, exist_ok=True)

    report = build_evidence_report()
    register = build_attachment_register()

    (out_dir / "evidence_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    (out_dir / "attachment_register.json").write_text(
        json.dumps(register, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    write_artifacts(Path.cwd())