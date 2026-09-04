from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.core.ids import deterministic_id
from smart_money.core.serialization import canonical_json
from smart_money.domain.solana_observation import (
    SolanaChainObservation,
    SolanaSlotCursor,
)

_SCHEMA_VERSION = "solana_slot_cursor_store.v1"


@dataclass(frozen=True, slots=True)
class SolanaSlotCursorReplayReceipt:
    stored_cursor_id: str
    replayed_cursor_id: str
    matches: bool
    schema_version: str = "solana_slot_cursor_replay.v1"

    def __post_init__(self) -> None:
        for name in ("stored_cursor_id", "replayed_cursor_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be a boolean")
        if self.schema_version != "solana_slot_cursor_replay.v1":
            raise ValueError("unsupported Solana slot cursor replay schema_version")
        expected = deterministic_id(
            "solana_slot_cursor_replay",
            {
                "replayed_cursor_id": self.replayed_cursor_id,
                "schema_version": self.schema_version,
                "stored_cursor_id": self.stored_cursor_id,
            },
        )
        if self.replay_id != expected:
            raise ValueError("replay_id does not match deterministic payload")

    @property
    def replay_id(self) -> str:
        return deterministic_id(
            "solana_slot_cursor_replay",
            {
                "replayed_cursor_id": self.replayed_cursor_id,
                "schema_version": self.schema_version,
                "stored_cursor_id": self.stored_cursor_id,
            },
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "matches": self.matches,
            "replayed_cursor_id": self.replayed_cursor_id,
            "replay_id": self.replay_id,
            "schema_version": self.schema_version,
            "stored_cursor_id": self.stored_cursor_id,
        }


class JsonSolanaSlotCursorStore:
    """Atomic persistence for one replay-safe Solana slot cursor."""

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._cursor = SolanaSlotCursor()
        self._load()

    def save(self, cursor: SolanaSlotCursor) -> str:
        if not isinstance(cursor, SolanaSlotCursor):
            raise TypeError("cursor must be a SolanaSlotCursor")
        self._persist(cursor)
        self._cursor = cursor
        return cursor.canonical_id

    def load(self) -> SolanaSlotCursor:
        return self._cursor

    @property
    def cursor_id(self) -> str:
        return self._cursor.canonical_id

    def replay(
        self,
        observation: SolanaChainObservation,
    ) -> SolanaSlotCursorReplayReceipt:
        if not isinstance(observation, SolanaChainObservation):
            raise TypeError("observation must be a SolanaChainObservation")
        replayed = SolanaSlotCursor.from_observation(observation)
        matches = self._cursor == replayed
        if not matches:
            raise ValueError("persisted Solana slot cursor does not match replay")
        return SolanaSlotCursorReplayReceipt(
            stored_cursor_id=self._cursor.canonical_id,
            replayed_cursor_id=replayed.canonical_id,
            matches=True,
        )

    def _load(self) -> None:
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        if self._file_path.is_file():
            source, recovering = self._file_path, False
        elif temporary.is_file():
            source, recovering = temporary, True
        else:
            return
        try:
            raw = source.read_text(encoding="utf-8")
            document: Any = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("Solana slot cursor store is not valid JSON") from exc
        if not isinstance(document, dict) or set(document) != {
            "cursor",
            "schema_version",
        }:
            raise ValueError("Solana slot cursor store keys do not match schema")
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError("unsupported Solana slot cursor store schema_version")
        cursor_data = document["cursor"]
        if not isinstance(cursor_data, dict):
            raise ValueError("Solana slot cursor must be a mapping")
        try:
            cursor = SolanaSlotCursor(
                slot=cursor_data["slot"],
                observed_at=cursor_data["observed_at"],
                transaction_signature=cursor_data["transaction_signature"],
                schema_version=cursor_data["schema_version"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid Solana slot cursor") from exc
        if canonical_json(document) != raw:
            raise ValueError("Solana slot cursor store is not canonical JSON")
        if recovering:
            atomic_replace(temporary, self._file_path)
        self._cursor = cursor

    def _persist(self, cursor: SolanaSlotCursor) -> None:
        if self._file_path.parent != Path("."):
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
        document = {
            "cursor": cursor.canonical_dict(),
            "schema_version": _SCHEMA_VERSION,
        }
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)


__all__ = ["JsonSolanaSlotCursorStore", "SolanaSlotCursorReplayReceipt"]
