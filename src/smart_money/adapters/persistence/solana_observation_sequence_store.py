from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.core.serialization import canonical_json
from smart_money.domain.solana_observation import (
    SolanaChainObservation,
    SolanaOrderingReplayReceipt,
    replay_solana_observation_order,
)

_SCHEMA_VERSION = "solana_observation_sequence_store.v1"


def _digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class JsonSolanaObservationSequenceStore:
    """Atomic append-only persistence for Solana ordering replay receipts."""

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._receipts: dict[str, SolanaOrderingReplayReceipt] = {}
        self._load()

    def append(self, receipt: SolanaOrderingReplayReceipt) -> str:
        if not isinstance(receipt, SolanaOrderingReplayReceipt):
            raise TypeError("receipt must be a SolanaOrderingReplayReceipt")
        existing = self._receipts.get(receipt.sequence_id)
        if existing is not None:
            if existing != receipt:
                raise RuntimeError("Solana ordering sequence identity collision")
            return receipt.sequence_id
        candidate = dict(self._receipts)
        candidate[receipt.sequence_id] = receipt
        self._persist(tuple(candidate.values()))
        self._receipts = candidate
        return receipt.sequence_id

    def get(self, sequence_id: str) -> SolanaOrderingReplayReceipt | None:
        return self._receipts.get(sequence_id)

    def iter_receipts(self) -> Iterator[SolanaOrderingReplayReceipt]:
        return iter(tuple(self._receipts.values()))

    @property
    def receipt_count(self) -> int:
        return len(self._receipts)

    @property
    def content_hash(self) -> str:
        return _digest([item.canonical_dict() for item in self._receipts.values()])

    def replay(
        self,
        observations: tuple[SolanaChainObservation, ...],
    ) -> SolanaOrderingReplayReceipt:
        """Verify a persisted sequence against freshly replayed observations."""
        expected = replay_solana_observation_order(observations)
        retained = self._receipts.get(expected.sequence_id)
        if retained is None:
            raise ValueError("persisted Solana ordering sequence is missing")
        if retained.canonical_dict() != expected.canonical_dict():
            raise ValueError("persisted Solana ordering sequence does not match replay")
        return retained

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
            raise ValueError("Solana observation sequence store is not valid JSON") from exc
        if not isinstance(document, dict) or set(document) != {
            "content_hash",
            "receipts",
            "schema_version",
        }:
            raise ValueError("Solana observation sequence store keys do not match schema")
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError("unsupported Solana observation sequence store schema_version")
        records = document["receipts"]
        if not isinstance(records, list) or _digest(records) != document["content_hash"]:
            raise ValueError("Solana observation sequence store content hash mismatch")
        if canonical_json(document) != raw:
            raise ValueError("Solana observation sequence store is not canonical JSON")
        loaded: dict[str, SolanaOrderingReplayReceipt] = {}
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("invalid Solana ordering replay receipt")
            try:
                receipt = SolanaOrderingReplayReceipt(
                    observation_ids=tuple(record["observation_ids"]),
                    first_ordering_key=tuple(record["first_ordering_key"]),
                    last_ordering_key=tuple(record["last_ordering_key"]),
                    sequence_id=record["sequence_id"],
                    schema_version=record["schema_version"],
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("invalid Solana ordering replay receipt") from exc
            if receipt.sequence_id in loaded:
                raise ValueError("duplicate Solana ordering sequence ID")
            loaded[receipt.sequence_id] = receipt
        if recovering:
            atomic_replace(temporary, self._file_path)
        self._receipts = loaded

    def _persist(self, receipts: tuple[SolanaOrderingReplayReceipt, ...]) -> None:
        if self._file_path.parent != Path("."):
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
        records = [item.canonical_dict() for item in receipts]
        document = {
            "content_hash": _digest(records),
            "receipts": records,
            "schema_version": _SCHEMA_VERSION,
        }
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)


__all__ = ["JsonSolanaObservationSequenceStore"]
