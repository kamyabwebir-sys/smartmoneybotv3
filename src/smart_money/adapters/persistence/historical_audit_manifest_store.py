from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.historical_receipt_audit import (
    HistoricalReceiptAuditManifest,
)
from smart_money.application.trusted_audit_head import TrustedAuditHead
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "historical_audit_manifest_store.v1"
_HEAD_STORE_SCHEMA_VERSION = "trusted_audit_head_store.v1"
_DOCUMENT_KEYS = frozenset({"schema_version", "content_hash", "manifests"})
_HEAD_DOCUMENT_KEYS = frozenset({"schema_version", "content_hash", "head"})
_HEAD_KEYS = frozenset(
    {
        "anchor_id",
        "manifest_store_hash",
        "manifest_count",
        "latest_audit_id",
        "previous_anchor_id",
        "schema_version",
    }
)
_MANIFEST_KEYS = frozenset(
    {
        "audit_id",
        "receipt_store_hash",
        "ledger_content_hash",
        "receipt_count",
        "current_count",
        "historically_valid_count",
        "drifted_count",
        "missing_count",
        "corrupted_count",
        "conflict_count",
        "assessment_ids",
        "rejected_receipt_ids",
        "schema_version",
    }
)
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class JsonHistoricalAuditManifestStore:
    """Atomic, append-only JSON persistence for historical audit manifests."""

    __slots__ = ("_file_path", "_manifests")

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._manifests: dict[str, HistoricalReceiptAuditManifest] = {}
        self._load_existing()

    def append(self, manifest: HistoricalReceiptAuditManifest) -> str:
        if not isinstance(manifest, HistoricalReceiptAuditManifest):
            raise TypeError(
                "manifest must be a HistoricalReceiptAuditManifest"
            )

        existing = self._manifests.get(manifest.audit_id)
        if existing is not None:
            if existing != manifest:
                raise RuntimeError("historical audit manifest identity collision")
            return manifest.audit_id

        candidate = dict(self._manifests)
        candidate[manifest.audit_id] = manifest
        self._persist(tuple(candidate.values()))
        self._manifests = candidate
        return manifest.audit_id

    def get(
        self,
        audit_id: str,
    ) -> HistoricalReceiptAuditManifest | None:
        return self._manifests.get(audit_id)

    def iter_manifests(self) -> Iterator[HistoricalReceiptAuditManifest]:
        return iter(tuple(self._manifests.values()))

    @property
    def manifest_count(self) -> int:
        return len(self._manifests)

    @property
    def content_hash(self) -> str:
        return self._compute_content_hash(
            self._serialize_manifests(tuple(self._manifests.values()))
        )

    @property
    def file_path(self) -> Path:
        return self._file_path

    def contains_content_hash(
        self,
        content_hash: str,
        manifest_count: int,
    ) -> bool:
        if not isinstance(content_hash, str):
            raise TypeError("content_hash must be a string")
        digest = content_hash.strip()
        if _SHA256_PATTERN.fullmatch(digest) is None:
            raise ValueError(
                "content_hash must be a lowercase SHA-256 hex digest"
            )
        if isinstance(manifest_count, bool) or not isinstance(
            manifest_count,
            int,
        ):
            raise TypeError("manifest_count must be an integer")
        if manifest_count < 0:
            raise ValueError("manifest_count must be non-negative")
        if manifest_count > self.manifest_count:
            return False
        prefix = tuple(self._manifests.values())[:manifest_count]
        prefix_hash = self._compute_content_hash(
            self._serialize_manifests(prefix)
        )
        return hmac.compare_digest(prefix_hash, digest)

    def _load_existing(self) -> None:
        temporary_path = self._temporary_path()
        recovering_temporary_file = False
        if self._file_path.is_file():
            source_path = self._file_path
        elif temporary_path.is_file():
            source_path = temporary_path
            recovering_temporary_file = True
        else:
            return

        try:
            loaded = self._load_from_path(source_path)
        except ValueError as exc:
            if recovering_temporary_file:
                raise ValueError(
                    "temporary historical audit recovery failed: "
                    f"{temporary_path}"
                ) from exc
            raise
        if recovering_temporary_file:
            atomic_replace(temporary_path, self._file_path)
        self._manifests = loaded

    def _load_from_path(
        self,
        path: Path,
    ) -> dict[str, HistoricalReceiptAuditManifest]:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"historical audit store is not valid JSON: {path}"
            ) from exc
        if not isinstance(document, dict):
            raise ValueError("historical audit store root must be an object")
        if set(document) != _DOCUMENT_KEYS:
            raise ValueError(
                "historical audit document keys do not match schema"
            )
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError(
                "unsupported historical audit store schema_version: "
                f"{document['schema_version']}"
            )

        manifests_data = document["manifests"]
        if not isinstance(manifests_data, list):
            raise ValueError("historical audit manifests must be a list")
        for manifest_data in manifests_data:
            self._validate_manifest_shape(manifest_data)

        content_hash = document["content_hash"]
        if (
            not isinstance(content_hash, str)
            or _SHA256_PATTERN.fullmatch(content_hash) is None
        ):
            raise ValueError(
                "content_hash must be a lowercase SHA-256 hex digest"
            )
        expected_hash = self._compute_content_hash(manifests_data)
        if not hmac.compare_digest(content_hash, expected_hash):
            raise ValueError("historical audit store content hash mismatch")

        loaded: dict[str, HistoricalReceiptAuditManifest] = {}
        for manifest_data in manifests_data:
            constructor_data = {
                **manifest_data,
                "assessment_ids": tuple(manifest_data["assessment_ids"]),
                "rejected_receipt_ids": tuple(
                    manifest_data["rejected_receipt_ids"]
                ),
            }
            try:
                manifest = HistoricalReceiptAuditManifest(
                    **constructor_data
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "invalid historical receipt audit manifest"
                ) from exc
            if manifest.audit_id in loaded:
                raise ValueError(
                    "duplicate historical audit manifest identity: "
                    f"{manifest.audit_id}"
                )
            loaded[manifest.audit_id] = manifest
        return loaded

    @staticmethod
    def _validate_manifest_shape(manifest: Any) -> None:
        if not isinstance(manifest, dict):
            raise ValueError("each historical audit manifest must be an object")
        if set(manifest) != _MANIFEST_KEYS:
            raise ValueError(
                "historical audit manifest keys do not match schema"
            )
        for field_name in ("assessment_ids", "rejected_receipt_ids"):
            values = manifest[field_name]
            if not isinstance(values, list) or not all(
                isinstance(value, str) for value in values
            ):
                raise ValueError(
                    f"historical audit {field_name} must be a string list"
                )

    def _persist(
        self,
        manifests: tuple[HistoricalReceiptAuditManifest, ...],
    ) -> None:
        if self._file_path.parent != Path("."):
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
        manifests_data = self._serialize_manifests(manifests)
        document = {
            "schema_version": _SCHEMA_VERSION,
            "content_hash": self._compute_content_hash(manifests_data),
            "manifests": manifests_data,
        }
        temporary_path = self._temporary_path()
        with temporary_path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary_path, self._file_path)

    @staticmethod
    def _serialize_manifests(
        manifests: tuple[HistoricalReceiptAuditManifest, ...],
    ) -> list[dict[str, Any]]:
        return [manifest.canonical_dict() for manifest in manifests]

    @staticmethod
    def _compute_content_hash(
        manifests_data: list[dict[str, Any]],
    ) -> str:
        material = {
            "schema_version": _SCHEMA_VERSION,
            "manifests": manifests_data,
        }
        return hashlib.sha256(
            canonical_json(material).encode("utf-8")
        ).hexdigest()

    def _temporary_path(self) -> Path:
        return self._file_path.with_name(f"{self._file_path.name}.tmp")


class JsonTrustedAuditHeadStore:
    """Atomic single-head persistence intended for a separately trusted path."""

    __slots__ = ("_file_path",)

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)

    def save(self, head: TrustedAuditHead) -> str:
        if not isinstance(head, TrustedAuditHead):
            raise TypeError("head must be a TrustedAuditHead")
        try:
            current = self.load()
        except FileNotFoundError:
            current = None

        if current is not None:
            if current == head:
                return head.anchor_id
            if head.previous_anchor_id != current.anchor_id:
                raise RuntimeError("trusted audit head chain mismatch")
            if head.manifest_count <= current.manifest_count:
                raise RuntimeError("trusted audit head must advance monotonically")
        elif head.previous_anchor_id is not None:
            raise RuntimeError("initial trusted audit head cannot have a parent")

        self._persist(head)
        return head.anchor_id

    def load(self) -> TrustedAuditHead:
        temporary_path = self._temporary_path()
        recovering_temporary_file = False
        if self._file_path.is_file():
            source_path = self._file_path
        elif temporary_path.is_file():
            source_path = temporary_path
            recovering_temporary_file = True
        else:
            raise FileNotFoundError(
                f"trusted audit head not found: {self._file_path}"
            )

        try:
            head = self._load_from_path(source_path)
        except ValueError as exc:
            if recovering_temporary_file:
                raise ValueError(
                    f"temporary trusted audit head recovery failed: "
                    f"{temporary_path}"
                ) from exc
            raise
        if recovering_temporary_file:
            atomic_replace(temporary_path, self._file_path)
        return head

    @property
    def file_path(self) -> Path:
        return self._file_path

    def _persist(self, head: TrustedAuditHead) -> None:
        if self._file_path.parent != Path("."):
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
        head_data = head.canonical_dict()
        document = {
            "schema_version": _HEAD_STORE_SCHEMA_VERSION,
            "content_hash": self._compute_head_hash(head_data),
            "head": head_data,
        }
        temporary_path = self._temporary_path()
        with temporary_path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary_path, self._file_path)

    def _load_from_path(self, path: Path) -> TrustedAuditHead:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"trusted audit head is not valid JSON: {path}"
            ) from exc
        if not isinstance(document, dict):
            raise ValueError("trusted audit head root must be an object")
        if set(document) != _HEAD_DOCUMENT_KEYS:
            raise ValueError("trusted audit head document keys do not match")
        if document["schema_version"] != _HEAD_STORE_SCHEMA_VERSION:
            raise ValueError(
                "unsupported trusted audit head store schema_version"
            )
        head_data = document["head"]
        if not isinstance(head_data, dict) or set(head_data) != _HEAD_KEYS:
            raise ValueError("trusted audit head keys do not match schema")
        content_hash = document["content_hash"]
        if (
            not isinstance(content_hash, str)
            or _SHA256_PATTERN.fullmatch(content_hash) is None
        ):
            raise ValueError(
                "trusted head content_hash must be a lowercase SHA-256 digest"
            )
        if not hmac.compare_digest(
            content_hash,
            self._compute_head_hash(head_data),
        ):
            raise ValueError("trusted audit head content hash mismatch")
        try:
            return TrustedAuditHead(**head_data)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid trusted audit head payload") from exc

    @staticmethod
    def _compute_head_hash(head_data: dict[str, Any]) -> str:
        material = {
            "schema_version": _HEAD_STORE_SCHEMA_VERSION,
            "head": head_data,
        }
        return hashlib.sha256(
            canonical_json(material).encode("utf-8")
        ).hexdigest()

    def _temporary_path(self) -> Path:
        return self._file_path.with_name(f"{self._file_path.name}.tmp")


__all__ = [
    "JsonHistoricalAuditManifestStore",
    "JsonTrustedAuditHeadStore",
]
