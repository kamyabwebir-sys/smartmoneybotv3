from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from contracts import EvidencePayload, GroundedEntry
from smart_money.core.serialization import canonicalize


_SCHEMA_VERSION = "evidence_ledger.v1"


class EvidenceGroundingLedger:
    """Append-only content-addressed evidence ledger with strict persistence."""

    def __init__(self) -> None:
        self._entries: dict[str, GroundedEntry] = {}
        self._processed_ids: set[str] = set()

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

    def save_to_disk(self, file_path: str | os.PathLike[str]) -> None:
        path = Path(file_path)
        if path.parent != Path("."):
            path.parent.mkdir(parents=True, exist_ok=True)

        document = {
            "schema_version": _SCHEMA_VERSION,
            "entries": [
                {
                    "canonical_id": entry.canonical_id,
                    "payload": canonicalize(entry.payload.canonical_dict()),
                }
                for entry in self._entries.values()
            ],
        }
        serialized = json.dumps(
            document,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )

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
        if (
            isinstance(document, dict)
            and document.get("schema_version") == _SCHEMA_VERSION
        ):
            entries = document.get("entries")
            if not isinstance(entries, list):
                raise ValueError("ledger entries must be a list")
            if not all(isinstance(entry, dict) for entry in entries):
                raise ValueError("each ledger entry must be an object")
            return entries

        if isinstance(document, dict):
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

        raise ValueError("ledger root must be an object")

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
        return len(self._entries)
