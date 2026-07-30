from __future__ import annotations

import importlib.util
from pathlib import Path


def load_verifier_module():
    verifier_path = Path.cwd() / "tests" / "discovery" / "em003_verifier.py"
    spec = importlib.util.spec_from_file_location("em003_verifier", verifier_path)

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_em003_report_is_governance_safe() -> None:
    verifier = load_verifier_module()
    report = verifier.build_evidence_report()

    assert report["em_id"] == "EM-003"
    assert report["status"] == "PARTIAL"
    assert report["approval_status"] == "NOT_APPROVED"
    assert report["promotion_gate"] == "LOCKED"
    assert report["implementation_authority"] == "NONE"
    assert report["deterministic"] is True
    assert report["replayable"] is True


def test_em003_cases_are_deterministic() -> None:
    verifier = load_verifier_module()

    first = verifier.build_evidence_report()
    second = verifier.build_evidence_report()

    assert first == second
    assert len(first["cases"]) == 10
    assert first["cases"][0]["id"] == "EM003-CASE-001"
    assert first["cases"][-1]["id"] == "EM003-CASE-010"


def test_em003_attachment_register_is_scaffold_only() -> None:
    verifier = load_verifier_module()
    register = verifier.build_attachment_register()

    assert register["em_id"] == "EM-003"
    assert register["artifacts"] == [
        "artifacts/discovery/em003/evidence_report.json",
        "artifacts/discovery/em003/attachment_register.json",
    ]