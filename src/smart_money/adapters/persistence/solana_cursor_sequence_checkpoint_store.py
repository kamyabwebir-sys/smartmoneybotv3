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
    SolanaCursorSequenceCheckpoint,
    SolanaOrderingReplayReceipt,
    SolanaSlotCursor,
)

_SCHEMA_VERSION = "solana_cursor_sequence_checkpoint_store.v1"


@dataclass(frozen=True, slots=True)
class SolanaCursorSequenceCheckpointReplayReceipt:
    stored_checkpoint_id: str
    replayed_checkpoint_id: str
    matches: bool
    schema_version: str = "solana_cursor_sequence_checkpoint_replay.v1"

    @property
    def replay_id(self) -> str:
        return deterministic_id(
            "solana_cursor_sequence_checkpoint_replay",
            {
                "replayed_checkpoint_id": self.replayed_checkpoint_id,
                "schema_version": self.schema_version,
                "stored_checkpoint_id": self.stored_checkpoint_id,
            },
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "matches": self.matches,
            "replayed_checkpoint_id": self.replayed_checkpoint_id,
            "replay_id": self.replay_id,
            "schema_version": self.schema_version,
            "stored_checkpoint_id": self.stored_checkpoint_id,
        }


class JsonSolanaCursorSequenceCheckpointStore:
    """Atomic persistence for one Solana cursor/sequence checkpoint."""

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._checkpoint: SolanaCursorSequenceCheckpoint | None = None
        self._load()

    def save(self, checkpoint: SolanaCursorSequenceCheckpoint) -> str:
        if not isinstance(checkpoint, SolanaCursorSequenceCheckpoint):
            raise TypeError("checkpoint must be a SolanaCursorSequenceCheckpoint")
        if (
            self._checkpoint is not None
            and self._checkpoint.checkpoint_id != checkpoint.checkpoint_id
        ):
            if self._checkpoint.canonical_dict() != checkpoint.canonical_dict():
                raise RuntimeError("Solana checkpoint identity collision")
        self._persist(checkpoint)
        self._checkpoint = checkpoint
        return checkpoint.checkpoint_id

    def load(self) -> SolanaCursorSequenceCheckpoint | None:
        return self._checkpoint

    @property
    def checkpoint_id(self) -> str | None:
        return None if self._checkpoint is None else self._checkpoint.checkpoint_id

    def replay(
        self,
        sequence: SolanaOrderingReplayReceipt,
        cursor: SolanaSlotCursor,
    ) -> SolanaCursorSequenceCheckpointReplayReceipt:
        if self._checkpoint is None:
            raise ValueError("persisted Solana checkpoint is missing")
        expected = SolanaCursorSequenceCheckpoint.from_sequence(sequence, cursor)
        if self._checkpoint.canonical_dict() != expected.canonical_dict():
            raise ValueError("persisted Solana checkpoint does not match replay")
        return SolanaCursorSequenceCheckpointReplayReceipt(
            stored_checkpoint_id=self._checkpoint.checkpoint_id,
            replayed_checkpoint_id=expected.checkpoint_id,
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
            raise ValueError("Solana checkpoint store is not valid JSON") from exc
        if not isinstance(document, dict) or set(document) != {"checkpoint", "schema_version"}:
            raise ValueError("Solana checkpoint store keys do not match schema")
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError("unsupported Solana checkpoint store schema_version")
        data = document["checkpoint"]
        if data is None:
            checkpoint = None
        elif isinstance(data, dict):
            cursor_data = data.get("cursor")
            if not isinstance(cursor_data, dict):
                raise ValueError("invalid Solana checkpoint cursor")
            try:
                checkpoint = SolanaCursorSequenceCheckpoint(
                    cursor=SolanaSlotCursor(
                        slot=cursor_data["slot"],
                        observed_at=cursor_data["observed_at"],
                        transaction_signature=cursor_data["transaction_signature"],
                        schema_version=cursor_data["schema_version"],
                    ),
                    sequence_id=data["sequence_id"],
                    observation_count=data["observation_count"],
                    last_observation_id=data["last_observation_id"],
                    last_ordering_key=tuple(data["last_ordering_key"]),
                    checkpoint_id=data["checkpoint_id"],
                    schema_version=data["schema_version"],
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("invalid Solana cursor sequence checkpoint") from exc
        else:
            raise ValueError("invalid Solana checkpoint")
        if canonical_json(document) != raw:
            raise ValueError("Solana checkpoint store is not canonical JSON")
        if recovering:
            atomic_replace(temporary, self._file_path)
        self._checkpoint = checkpoint

    def _persist(self, checkpoint: SolanaCursorSequenceCheckpoint) -> None:
        if self._file_path.parent != Path("."):
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
        document = {
            "checkpoint": checkpoint.canonical_dict(),
            "schema_version": _SCHEMA_VERSION,
        }
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)


__all__ = [
    "JsonSolanaCursorSequenceCheckpointStore",
    "SolanaCursorSequenceCheckpointReplayReceipt",
]
