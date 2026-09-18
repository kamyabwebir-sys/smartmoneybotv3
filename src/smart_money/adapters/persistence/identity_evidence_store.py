from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.core.serialization import canonical_json
from smart_money.ingestion.contracts import EvidencePayload

_SCHEMA_VERSION = "identity_evidence_store.v1"


class JsonIdentityEvidenceStore:
    """Atomic, content-addressed persistence for identity EvidencePayloads."""

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._payloads: dict[str, EvidencePayload] = {}
        self._load()

    def append(self, payload: EvidencePayload) -> str:
        if not isinstance(payload, EvidencePayload):
            raise TypeError("payload must be an EvidencePayload")
        if payload.evidence_type != "identity_evidence":
            raise ValueError("payload must be identity evidence")
        identity = payload.get_canonical_id()
        existing = self._payloads.get(identity)
        if existing is not None:
            if existing != payload:
                raise RuntimeError("identity evidence identity collision")
            return identity
        candidate = dict(self._payloads)
        candidate[identity] = payload
        self._persist(tuple(candidate.values()))
        self._payloads = candidate
        return identity

    def get(self, evidence_id: str) -> EvidencePayload | None:
        return self._payloads.get(evidence_id)

    def iter_payloads(self) -> Iterator[EvidencePayload]:
        return iter(tuple(self._payloads.values()))

    @property
    def entry_count(self) -> int:
        return len(self._payloads)

    @property
    def content_hash(self) -> str:
        return _digest([item.canonical_dict() for item in self._payloads.values()])

    def _load(self) -> None:
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        if self._file_path.is_file():
            source, recovering = self._file_path, False
        elif temporary.is_file():
            source, recovering = temporary, True
        else:
            return
        try:
            document: Any = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("identity evidence store is not valid JSON") from exc
        if not isinstance(document, dict) or set(document) != {
            "content_hash",
            "payloads",
            "schema_version",
        }:
            raise ValueError("identity evidence store keys do not match schema")
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError("unsupported identity evidence store schema_version")
        records = document["payloads"]
        if not isinstance(records, list) or _digest(records) != document["content_hash"]:
            raise ValueError("identity evidence store content hash mismatch")
        if canonical_json(document) != source.read_text(encoding="utf-8"):
            raise ValueError("identity evidence store is not canonical JSON")
        loaded: dict[str, EvidencePayload] = {}
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("invalid identity evidence payload")
            try:
                payload = EvidencePayload(
                    source_id=record["source_id"],
                    evidence_type=record["evidence_type"],
                    timestamp=record["timestamp"],
                    data=record["data"],
                    metadata=record["metadata"],
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("invalid identity evidence payload") from exc
            if payload.evidence_type != "identity_evidence":
                raise ValueError("identity evidence store contains non-identity payload")
            identity = payload.get_canonical_id()
            if identity in loaded:
                raise ValueError("duplicate identity evidence ID")
            loaded[identity] = payload
        if recovering:
            atomic_replace(temporary, self._file_path)
        self._payloads = loaded

    def _persist(self, payloads: tuple[EvidencePayload, ...]) -> None:
        if self._file_path.parent != Path("."):
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
        records = [item.canonical_dict() for item in payloads]
        document = {
            "content_hash": _digest(records),
            "payloads": records,
            "schema_version": _SCHEMA_VERSION,
        }
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)


def _digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


__all__ = ["JsonIdentityEvidenceStore"]
