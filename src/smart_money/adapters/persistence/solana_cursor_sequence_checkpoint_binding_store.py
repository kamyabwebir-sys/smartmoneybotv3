from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.solana_cursor_sequence_checkpoint_binding import (
    SolanaCursorSequenceCheckpointBindingReceipt,
)
from smart_money.core.ids import deterministic_id
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "solana_cursor_sequence_checkpoint_binding_store.v1"


@dataclass(frozen=True, slots=True)
class SolanaCursorSequenceCheckpointBindingStoreReplayReceipt:
    replay_id: str
    original_receipt_id: str
    matches: bool
    schema_version: str = "solana_cursor_sequence_checkpoint_binding_store_replay.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.original_receipt_id, str) or not self.original_receipt_id.strip():
            raise ValueError("original_receipt_id must be a non-empty string")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be a boolean")
        if self.schema_version != "solana_cursor_sequence_checkpoint_binding_store_replay.v1":
            raise ValueError("unsupported Solana binding store replay schema_version")
        expected = deterministic_id(
            "solana_cursor_sequence_checkpoint_binding_store_replay",
            {
                "original_receipt_id": self.original_receipt_id,
                "schema_version": self.schema_version,
            },
        )
        if self.replay_id != expected:
            raise ValueError("replay_id does not match deterministic payload")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "matches": self.matches,
            "original_receipt_id": self.original_receipt_id,
            "replay_id": self.replay_id,
            "schema_version": self.schema_version,
        }


class JsonSolanaCursorSequenceCheckpointBindingStore:
    """Atomic persistence for the latest cursor/sequence binding receipt."""

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._receipt: SolanaCursorSequenceCheckpointBindingReceipt | None = None
        self._load()

    def save(self, receipt: SolanaCursorSequenceCheckpointBindingReceipt) -> str:
        if not isinstance(receipt, SolanaCursorSequenceCheckpointBindingReceipt):
            raise TypeError("receipt must be a SolanaCursorSequenceCheckpointBindingReceipt")
        if self._receipt is not None and self._receipt != receipt:
            raise RuntimeError("Solana checkpoint binding identity collision")
        self._persist(receipt)
        self._receipt = receipt
        return receipt.receipt_id

    def load(self) -> SolanaCursorSequenceCheckpointBindingReceipt | None:
        return self._receipt

    @property
    def receipt_id(self) -> str | None:
        return None if self._receipt is None else self._receipt.receipt_id

    def replay(
        self, receipt: SolanaCursorSequenceCheckpointBindingReceipt
    ) -> SolanaCursorSequenceCheckpointBindingStoreReplayReceipt:
        if self._receipt is None:
            raise ValueError("persisted Solana binding receipt is missing")
        if not isinstance(receipt, SolanaCursorSequenceCheckpointBindingReceipt):
            raise TypeError("receipt must be a SolanaCursorSequenceCheckpointBindingReceipt")
        if self._receipt.canonical_dict() != receipt.canonical_dict():
            raise ValueError("persisted Solana binding receipt does not match replay")
        return SolanaCursorSequenceCheckpointBindingStoreReplayReceipt(
            replay_id=deterministic_id(
                "solana_cursor_sequence_checkpoint_binding_store_replay",
                {
                    "original_receipt_id": receipt.receipt_id,
                    "schema_version": "solana_cursor_sequence_checkpoint_binding_store_replay.v1",
                },
            ),
            original_receipt_id=receipt.receipt_id,
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
            raise ValueError("Solana binding store is not valid JSON") from exc
        if not isinstance(document, dict) or set(document) != {"receipt", "schema_version"}:
            raise ValueError("Solana binding store keys do not match schema")
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError("unsupported Solana binding store schema_version")
        data = document["receipt"]
        if not isinstance(data, dict):
            raise ValueError("invalid Solana checkpoint binding receipt")
        try:
            receipt = SolanaCursorSequenceCheckpointBindingReceipt(
                receipt_id=data["receipt_id"],
                previous_cursor_id=data["previous_cursor_id"],
                current_cursor_id=data["current_cursor_id"],
                sequence_id=data["sequence_id"],
                checkpoint_id=data["checkpoint_id"],
                observation_id=data["observation_id"],
                schema_version=data["schema_version"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid Solana checkpoint binding receipt") from exc
        if canonical_json(document) != raw:
            raise ValueError("Solana binding store is not canonical JSON")
        if recovering:
            atomic_replace(temporary, self._file_path)
        self._receipt = receipt

    def _persist(self, receipt: SolanaCursorSequenceCheckpointBindingReceipt) -> None:
        if self._file_path.parent != Path("."):
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
        document = {"receipt": receipt.canonical_dict(), "schema_version": _SCHEMA_VERSION}
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)


__all__ = [
    "JsonSolanaCursorSequenceCheckpointBindingStore",
    "SolanaCursorSequenceCheckpointBindingStoreReplayReceipt",
]
