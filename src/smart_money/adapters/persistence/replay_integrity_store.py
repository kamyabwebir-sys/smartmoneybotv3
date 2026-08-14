from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from pathlib import Path
from typing import Any

from smart_money.application.replay_integrity import ReplayIntegrityManifest
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "replay_integrity_receipt.v1"
_DOCUMENT_KEYS = frozenset({"schema_version", "content_hash", "manifest"})
_MANIFEST_KEYS = frozenset(
    {
        "integrity_id",
        "replay_manifest_id",
        "pipeline_version",
        "config_hash",
        "input_hash",
        "output_hash",
        "evidence_count",
        "schema_version",
    }
)
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class JsonReplayIntegrityStore:
    """Persist one replay integrity receipt as strict, byte-stable JSON."""

    def save(
        self,
        manifest: ReplayIntegrityManifest,
        file_path: str | os.PathLike[str],
    ) -> None:
        if not isinstance(manifest, ReplayIntegrityManifest):
            raise TypeError("manifest must be a ReplayIntegrityManifest")

        path = Path(file_path)
        if path.parent != Path("."):
            path.parent.mkdir(parents=True, exist_ok=True)

        manifest_data = manifest.canonical_dict()
        document = {
            "schema_version": _SCHEMA_VERSION,
            "content_hash": self._compute_content_hash(manifest_data),
            "manifest": manifest_data,
        }
        temporary_path = self._temporary_path(path)
        with temporary_path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)

    def load(
        self,
        file_path: str | os.PathLike[str],
    ) -> ReplayIntegrityManifest:
        path = Path(file_path)
        temporary_path = self._temporary_path(path)
        recovering_temporary_file = False

        if path.is_file():
            source_path = path
        elif temporary_path.is_file():
            source_path = temporary_path
            recovering_temporary_file = True
        else:
            raise FileNotFoundError(f"replay integrity receipt not found: {path}")

        try:
            manifest = self._load_from_path(source_path)
        except ValueError as exc:
            if recovering_temporary_file:
                raise ValueError(
                    f"temporary replay integrity recovery failed: {temporary_path}"
                ) from exc
            raise

        if recovering_temporary_file:
            os.replace(temporary_path, path)
        return manifest

    def _load_from_path(self, path: Path) -> ReplayIntegrityManifest:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"replay integrity receipt is not valid JSON: {path}"
            ) from exc

        if not isinstance(document, dict):
            raise ValueError("replay integrity receipt root must be an object")
        if set(document) != _DOCUMENT_KEYS:
            raise ValueError("replay integrity receipt document keys do not match schema")
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError(
                "unsupported replay integrity receipt schema_version: "
                f"{document['schema_version']}"
            )

        content_hash = document["content_hash"]
        if (
            not isinstance(content_hash, str)
            or _SHA256_PATTERN.fullmatch(content_hash) is None
        ):
            raise ValueError(
                "receipt content_hash must be a lowercase SHA-256 hex digest"
            )

        manifest_data = document["manifest"]
        if not isinstance(manifest_data, dict):
            raise ValueError("replay integrity manifest must be an object")
        if set(manifest_data) != _MANIFEST_KEYS:
            raise ValueError("replay integrity manifest keys do not match schema")

        expected_hash = self._compute_content_hash(manifest_data)
        if not hmac.compare_digest(content_hash, expected_hash):
            raise ValueError("replay integrity receipt content hash mismatch")

        try:
            return ReplayIntegrityManifest(**manifest_data)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid replay integrity manifest") from exc

    @staticmethod
    def _compute_content_hash(manifest_data: dict[str, Any]) -> str:
        hash_material = {
            "schema_version": _SCHEMA_VERSION,
            "manifest": manifest_data,
        }
        return hashlib.sha256(
            canonical_json(hash_material).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _temporary_path(path: Path) -> Path:
        return path.with_name(f"{path.name}.tmp")


__all__ = ["JsonReplayIntegrityStore"]
