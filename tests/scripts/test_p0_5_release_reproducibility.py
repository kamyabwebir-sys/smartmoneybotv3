from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.verify_p0_5_release_reproducibility import (
    _dependency_name,
    _version_tuple,
    verify,
)


def test_version_tuple_is_numeric_and_deterministic() -> None:
    assert _version_tuple("3.11") == (3, 11, 0)
    assert _version_tuple("0.12.0") == (0, 12, 0)


def test_dependency_name_normalizes_requirement() -> None:
    assert _dependency_name("Some_Package>=1.2") == "some-package"


def test_verifier_fails_closed_on_release_input_hash_drift(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "environment": {
                    "python_max_exclusive": "3.13",
                    "python_min": "3.11",
                    "uv_min": "0.12.0",
                },
                "expected_optional_dependencies": {},
                "files": {
                    "pyproject.toml": {
                        "sha256": "0" * 64,
                    }
                },
                "schema_version": (
                    "p0_5_release_reproducibility_manifest.v1"
                ),
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="release input hash mismatch: pyproject.toml",
    ):
        verify(tmp_path, manifest_path)
