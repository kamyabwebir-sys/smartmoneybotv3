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
from smart_money.application.durable_run_receipt_audit import (
    DurableRunReceiptAssessment,
    DurableRunReceiptAuditManifest,
    DurableRunReceiptStatus,
)
from smart_money.application.historical_commit_receipt import (
    HistoricalCommitStatus,
)
from smart_money.application.trusted_durable_run_audit_head import (
    TrustedDurableRunAuditHead,
)
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "durable_run_receipt_audit_manifest_store.v1"
_DOCUMENT_KEYS = frozenset({"schema_version", "content_hash", "manifests"})
_HEAD_SCHEMA_VERSION = "trusted_durable_run_audit_head_store.v1"
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class JsonDurableRunReceiptAuditManifestStore:
    """Byte-stable, atomic, append-only durable-run audit persistence."""

    __slots__ = ("_file_path", "_manifests")

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._manifests: dict[str, DurableRunReceiptAuditManifest] = {}
        self._load_existing()

    def append(self, manifest: DurableRunReceiptAuditManifest) -> str:
        if not isinstance(manifest, DurableRunReceiptAuditManifest):
            raise TypeError(
                "manifest must be a DurableRunReceiptAuditManifest"
            )
        existing = self._manifests.get(manifest.audit_id)
        if existing is not None:
            if existing != manifest:
                raise RuntimeError("durable-run audit identity collision")
            return manifest.audit_id
        candidate = dict(self._manifests)
        candidate[manifest.audit_id] = manifest
        self._persist(tuple(candidate.values()))
        self._manifests = candidate
        return manifest.audit_id

    def get(
        self,
        audit_id: str,
    ) -> DurableRunReceiptAuditManifest | None:
        return self._manifests.get(audit_id)

    def iter_manifests(
        self,
    ) -> Iterator[DurableRunReceiptAuditManifest]:
        return iter(tuple(self._manifests.values()))

    @property
    def manifest_count(self) -> int:
        return len(self._manifests)

    @property
    def content_hash(self) -> str:
        return self._compute_hash(self._serialize(tuple(self._manifests.values())))

    def contains_content_hash(
        self,
        content_hash: str,
        manifest_count: int,
    ) -> bool:
        if (
            not isinstance(content_hash, str)
            or _SHA256_PATTERN.fullmatch(content_hash) is None
        ):
            raise ValueError("content_hash must be a lowercase SHA-256 digest")
        if isinstance(manifest_count, bool) or not isinstance(manifest_count, int):
            raise TypeError("manifest_count must be an integer")
        if manifest_count < 0:
            raise ValueError("manifest_count must be non-negative")
        if manifest_count > self.manifest_count:
            return False
        prefix = tuple(self._manifests.values())[:manifest_count]
        return hmac.compare_digest(
            self._compute_hash(self._serialize(prefix)),
            content_hash,
        )

    def _load_existing(self) -> None:
        temporary = self._temporary_path()
        recovering = not self._file_path.is_file() and temporary.is_file()
        source = temporary if recovering else self._file_path
        if not source.is_file():
            return
        try:
            loaded = self._load(source)
        except ValueError as exc:
            if recovering:
                raise ValueError(
                    f"temporary durable-run audit recovery failed: {temporary}"
                ) from exc
            raise
        if recovering:
            atomic_replace(temporary, self._file_path)
        self._manifests = loaded

    def _load(
        self,
        path: Path,
    ) -> dict[str, DurableRunReceiptAuditManifest]:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("durable-run audit store is not valid JSON") from exc
        if (
            not isinstance(document, dict)
            or set(document) != _DOCUMENT_KEYS
            or document["schema_version"] != _SCHEMA_VERSION
        ):
            raise ValueError("durable-run audit store schema mismatch")
        rows = document["manifests"]
        if not isinstance(rows, list):
            raise ValueError("durable-run audit manifests must be a list")
        digest = document["content_hash"]
        if (
            not isinstance(digest, str)
            or _SHA256_PATTERN.fullmatch(digest) is None
            or not hmac.compare_digest(digest, self._compute_hash(rows))
        ):
            raise ValueError("durable-run audit store content hash mismatch")
        loaded: dict[str, DurableRunReceiptAuditManifest] = {}
        for row in rows:
            manifest = self._decode_manifest(row)
            if manifest.audit_id in loaded:
                raise ValueError("duplicate durable-run audit identity")
            loaded[manifest.audit_id] = manifest
        return loaded

    @staticmethod
    def _decode_manifest(row: Any) -> DurableRunReceiptAuditManifest:
        if not isinstance(row, dict):
            raise ValueError("durable-run audit manifest must be an object")
        try:
            assessments = tuple(
                DurableRunReceiptAssessment(
                    **{
                        **value,
                        "status": DurableRunReceiptStatus(value["status"]),
                        "commit_status": (
                            None
                            if value["commit_status"] is None
                            else HistoricalCommitStatus(value["commit_status"])
                        ),
                    }
                )
                for value in row["assessments"]
            )
            return DurableRunReceiptAuditManifest(
                **{
                    **row,
                    "assessments": assessments,
                    "rejected_run_ids": tuple(row["rejected_run_ids"]),
                }
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid durable-run audit manifest") from exc

    def _persist(
        self,
        manifests: tuple[DurableRunReceiptAuditManifest, ...],
    ) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        rows = self._serialize(manifests)
        document = {
            "schema_version": _SCHEMA_VERSION,
            "content_hash": self._compute_hash(rows),
            "manifests": rows,
        }
        temporary = self._temporary_path()
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)

    @staticmethod
    def _serialize(
        manifests: tuple[DurableRunReceiptAuditManifest, ...],
    ) -> list[dict[str, Any]]:
        return [manifest.canonical_dict() for manifest in manifests]

    @staticmethod
    def _compute_hash(rows: list[dict[str, Any]]) -> str:
        return hashlib.sha256(
            canonical_json(
                {"schema_version": _SCHEMA_VERSION, "manifests": rows}
            ).encode("utf-8")
        ).hexdigest()

    def _temporary_path(self) -> Path:
        return self._file_path.with_name(f"{self._file_path.name}.tmp")


class JsonTrustedDurableRunAuditHeadStore:
    __slots__ = ("_file_path",)

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)

    def save(self, head: TrustedDurableRunAuditHead) -> str:
        try:
            current = self.load()
        except FileNotFoundError:
            current = None
        if current is not None and current != head:
            if (
                head.previous_anchor_id != current.anchor_id
                or head.manifest_count <= current.manifest_count
            ):
                raise RuntimeError("trusted durable-run head chain mismatch")
        elif current is None and head.previous_anchor_id is not None:
            raise RuntimeError("initial trusted head cannot have a parent")
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        data = head.canonical_dict()
        document = {
            "schema_version": _HEAD_SCHEMA_VERSION,
            "content_hash": hashlib.sha256(
                canonical_json(data).encode("utf-8")
            ).hexdigest(),
            "head": data,
        }
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)
        return head.anchor_id

    def load(self) -> TrustedDurableRunAuditHead:
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        recovering = not self._file_path.is_file() and temporary.is_file()
        path = temporary if recovering else self._file_path
        if not path.is_file():
            raise FileNotFoundError(f"trusted durable-run head not found: {path}")
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            data = document["head"]
            expected = hashlib.sha256(
                canonical_json(data).encode("utf-8")
            ).hexdigest()
            if (
                document["schema_version"] != _HEAD_SCHEMA_VERSION
                or not hmac.compare_digest(document["content_hash"], expected)
            ):
                raise ValueError("trusted durable-run head content mismatch")
            head = TrustedDurableRunAuditHead(**data)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("invalid trusted durable-run head") from exc
        if recovering:
            atomic_replace(temporary, self._file_path)
        return head


__all__ = [
    "JsonDurableRunReceiptAuditManifestStore",
    "JsonTrustedDurableRunAuditHeadStore",
]
