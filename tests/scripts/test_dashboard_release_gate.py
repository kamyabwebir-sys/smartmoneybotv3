from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / "scripts" / "dashboard_release_gate.py"


def load_gate():
    specification = importlib.util.spec_from_file_location(
        "dashboard_release_gate",
        GATE_PATH,
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_dashboard_gate_collects_canonical_dashboard_tests() -> None:
    gate = load_gate()

    targets = gate.collect_paths(ROOT, gate.TEST_PATTERNS)

    assert targets
    assert all(path.is_file() for path in targets)
    assert all(
        path.as_posix().startswith(
            (
                f"{ROOT.as_posix()}/tests/application/",
                f"{ROOT.as_posix()}/tests/adapters/persistence/",
            )
        )
        for path in targets
    )


def test_dashboard_gate_hash_is_prefixed_sha256() -> None:
    gate = load_gate()

    digest = gate.sha256_file(GATE_PATH)

    assert digest.startswith("sha256:")
    assert len(digest) == 71