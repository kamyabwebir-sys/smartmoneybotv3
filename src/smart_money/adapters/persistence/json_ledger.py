from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from smart_money.core.serialization import canonicalize
from smart_money.ingestion.contracts import EvidencePayload

_SCHEMA_VERSION = "evidence_ledger.v2"
_LEGACY_SCHEMA_VERSION = "evidence_ledger.v1"
_V2_DOCUMENT_KEYS = frozenset({"schema_version", "content_hash", "entries"})
_V1_DOCUMENT_KEYS = frozenset({"schema_version", "entries"})
_ENTRY_KEYS = frozenset({"canonical_id", "payload"})
_PAYLOAD_KEYS = frozenset(
    {"source_id", "evidence_type", "timestamp", "data", "metadata"}
)


@dataclass(frozen=True, slots=True)
class GroundedEntry:
    canonical_id: str
    payload: EvidencePayload

    def __post_init__(self) -> None:
        if not isinstance(self.canonical_id, str) or not self.canonical_id.strip():
            raise ValueError("canonical_id must be a non-empty string")
        if not isinstance(self.payload, EvidencePayload):
            raise TypeError("payload must be an EvidencePayload")
        if self.canonical_id != self.payload.get_canonical_id():
            raise ValueError("canonical_id does not match payload content")


class EvidenceGroundingLedger:
    """Append-only content-addressed evidence ledger with strict JSON persistence."""

    def __init__(self) -> None:
        self._entries: dict[str, GroundedEntry] = {}
        self._processed_ids: set[str] = set()

    def append(self, payload: EvidencePayload) -> str:
        return self.record(payload)

    def record(self, payload: EvidencePayload) -> str:
        if not isinstance(payload, EvidencePayload):
            raise TypeError("payload must be an EvidencePayload")

        canonical_id = payload.get_canonical_id()
        if canonical_id not in self._entries:
            self._entries[canonical_id] = GroundedEntry(
                canonical_id=canonical_id,
                payload=payload,
            )
        return canonical_id

    def contains(self, canonical_id: str) -> bool:
        return canonical_id in self._entries

    def get(self, canonical_id: str) -> EvidencePayload | None:
        entry = self._entries.get(canonical_id)
        return None if entry is None else entry.payload

    def iter_payloads(self) -> Iterator[EvidencePayload]:
        return iter(tuple(entry.payload for entry in self._entries.values()))

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    @property
    def content_hash(self) -> str:
        return self._compute_content_hash(self._serialize_entries())

    def save_to_disk(self, file_path: str | os.PathLike[str]) -> None:
        path = Path(file_path)
        if path.parent != Path("."):
            path.parent.mkdir(parents=True, exist_ok=True)

        entries = self._serialize_entries()
        document = {
            "schema_version": _SCHEMA_VERSION,
            "content_hash": self._compute_content_hash(entries),
            "entries": entries,
        }
        serialized = self._canonical_json(document)

        temporary_path = path.with_name(f"{path.name}.tmp")
        temporary_path.write_text(serialized, encoding="utf-8")
        os.replace(temporary_path, path)

    def load_from_disk(self, file_path: str | os.PathLike[str]) -> None:
        path = Path(file_path)
        if not path.exists():
            return

        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"ledger file is not valid JSON: {path}") from exc

        serialized_entries = self._extract_entries(document)
        loaded: dict[str, GroundedEntry] = {}
        for raw_entry in serialized_entries:
            entry = self._deserialize_entry(raw_entry)
            if entry.canonical_id in loaded:
                raise ValueError(
                    f"duplicate canonical_id in ledger: {entry.canonical_id}"
                )
            loaded[entry.canonical_id] = entry

        self._entries = loaded
        self._processed_ids.clear()

    def _extract_entries(self, document: Any) -> list[dict[str, Any]]:
        if not isinstance(document, dict):
            raise ValueError("ledger root must be an object")

        if "schema_version" in document:
            schema_version = document["schema_version"]
            if schema_version not in {_SCHEMA_VERSION, _LEGACY_SCHEMA_VERSION}:
                raise ValueError(f"unsupported ledger schema_version: {schema_version}")

            expected_keys = (
                _V2_DOCUMENT_KEYS
                if schema_version == _SCHEMA_VERSION
                else _V1_DOCUMENT_KEYS
            )
            if set(document) != expected_keys:
                raise ValueError(
                    f"{schema_version} ledger document keys do not match schema"
                )

            entries = document.get("entries")
            if not isinstance(entries, list):
                raise ValueError("ledger entries must be a list")
            self._validate_entries(
                entries,
                require_metadata=schema_version == _SCHEMA_VERSION,
            )

            if schema_version == _SCHEMA_VERSION:
                content_hash = document.get("content_hash")
                if not isinstance(content_hash, str) or re.fullmatch(
                    r"[0-9a-f]{64}",
                    content_hash,
                ) is None:
                    raise ValueError(
                        "ledger content_hash must be a lowercase SHA-256 hex digest"
                    )
                expected_hash = self._compute_content_hash(entries)
                if not hmac.compare_digest(content_hash, expected_hash):
                    raise ValueError("ledger content hash mismatch")
            return entries

        legacy_entries: list[dict[str, Any]] = []
        for canonical_id, payload in document.items():
            if not isinstance(payload, dict):
                raise ValueError("legacy ledger payloads must be objects")
            legacy_entries.append(
                {
                    "canonical_id": canonical_id,
                    "payload": payload,
                }
            )
        return legacy_entries

    @staticmethod
    def _validate_entries(
        entries: list[Any],
        *,
        require_metadata: bool,
    ) -> None:
        for raw_entry in entries:
            if not isinstance(raw_entry, dict):
                raise ValueError("each ledger entry must be an object")
            if set(raw_entry) != _ENTRY_KEYS:
                raise ValueError("ledger entry keys do not match schema")

            payload = raw_entry["payload"]
            if not isinstance(payload, dict):
                raise ValueError("ledger entry payload must be an object")

            payload_keys = set(payload)
            required_keys = (
                _PAYLOAD_KEYS
                if require_metadata
                else _PAYLOAD_KEYS - {"metadata"}
            )
            if not required_keys.issubset(payload_keys) or not payload_keys.issubset(
                _PAYLOAD_KEYS
            ):
                raise ValueError("ledger payload keys do not match schema")

    def _serialize_entries(self) -> list[dict[str, Any]]:
        return [
            {
                "canonical_id": entry.canonical_id,
                "payload": canonicalize(entry.payload.canonical_dict()),
            }
            for entry in self._entries.values()
        ]

    @staticmethod
    def _canonical_json(value: Any) -> str:
        return json.dumps(
            value,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )

    @classmethod
    def _compute_content_hash(cls, entries: list[dict[str, Any]]) -> str:
        hash_material = {
            "schema_version": _SCHEMA_VERSION,
            "entries": entries,
        }
        encoded = cls._canonical_json(hash_material).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _deserialize_entry(self, raw_entry: dict[str, Any]) -> GroundedEntry:
        canonical_id = raw_entry.get("canonical_id")
        payload_data = raw_entry.get("payload")
        if not isinstance(canonical_id, str) or not isinstance(payload_data, dict):
            raise ValueError("ledger entry is missing canonical_id or payload")

        try:
            payload = EvidencePayload(
                source_id=payload_data["source_id"],
                evidence_type=payload_data["evidence_type"],
                timestamp=payload_data["timestamp"],
                data=payload_data["data"],
                metadata=payload_data.get("metadata", {}),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid ledger payload for {canonical_id}") from exc

        if canonical_id != payload.get_canonical_id():
            raise ValueError(
                f"ledger identity mismatch for canonical_id: {canonical_id}"
            )
        return GroundedEntry(canonical_id=canonical_id, payload=payload)

    def get_entry(self, canonical_id: str) -> GroundedEntry | None:
        return self._entries.get(canonical_id)

    def get_all_entries(self) -> Iterator[GroundedEntry]:
        return iter(tuple(self._entries.values()))

    def get_unprocessed_entries(self) -> Iterator[GroundedEntry]:
        return (
            entry
            for entry in tuple(self._entries.values())
            if entry.canonical_id not in self._processed_ids
        )

    def mark_processed(self, canonical_id: str) -> None:
        if canonical_id not in self._entries:
            raise KeyError(f"unknown canonical_id: {canonical_id}")
        self._processed_ids.add(canonical_id)

    @property
    def count(self) -> int:
        return self.entry_count


__all__ = ["EvidenceGroundingLedger", "GroundedEntry"]
