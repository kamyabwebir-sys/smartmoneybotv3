from __future__ import annotations

from pathlib import Path

import pytest

from scripts.verify_p0_6_release_bundle_offline import verify_bundle_hashes


def test_bundle_hash_verification_accepts_matching_input(tmp_path: Path) -> None:
    payload = tmp_path / "payload.txt"
    payload.write_text("stable", encoding="utf-8")
    manifest = {
        "bundle_inputs": {
            "payload.txt": (
                "f379ccb92b911644767b92b66e2b8d9f4f8d1c4dce4e68e6c4a7f1d2f1f5b162"
            )
        },
        "schema_version": "p0_6_release_bundle_manifest.v1",
    }

    import hashlib

    manifest["bundle_inputs"]["payload.txt"] = hashlib.sha256(
        payload.read_bytes()
    ).hexdigest()
    assert verify_bundle_hashes(tmp_path, manifest) == 1


def test_bundle_hash_verification_fails_closed_on_drift(tmp_path: Path) -> None:
    payload = tmp_path / "payload.txt"
    payload.write_text("changed", encoding="utf-8")
    manifest = {
        "bundle_inputs": {"payload.txt": "0" * 64},
        "schema_version": "p0_6_release_bundle_manifest.v1",
    }

    with pytest.raises(
        ValueError,
        match="release bundle input hash mismatch: payload.txt",
    ):
        verify_bundle_hashes(tmp_path, manifest)
