from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.solana_observation_parser import SolanaObservationParser
from smart_money.core.ids import deterministic_id
from smart_money.core.serialization import canonical_json
from smart_money.domain.solana_observation import SolanaChainObservation
from smart_money.ingestion.contracts import EvidencePayload

_SCHEMA_VERSION = "solana_observation_store.v1"


def _digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class SolanaObservationStoreReplayReceipt:
    """Deterministic proof that a persisted Solana payload replays identically."""

    __slots__ = (
        "receipt_id",
        "observation_id",
        "evidence_id",
        "content_hash",
        "matches",
        "schema_version",
    )

    def __init__(
        self,
        *,
        observation_id: str,
        evidence_id: str,
        content_hash: str,
        matches: bool,
        schema_version: str = "solana_observation_store_replay.v1",
    ) -> None:
        for name in ("observation_id", "evidence_id", "content_hash"):
            value = locals()[name]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if len(content_hash) != 64:
            raise ValueError("content_hash must be a SHA-256 hex digest")
        if not isinstance(matches, bool):
            raise TypeError("matches must be a boolean")
        if schema_version != "solana_observation_store_replay.v1":
            raise ValueError("unsupported Solana store replay schema_version")
        identity = {
            "content_hash": content_hash,
            "evidence_id": evidence_id,
            "observation_id": observation_id,
            "schema_version": schema_version,
        }
        self.receipt_id = deterministic_id("solana_observation_store_replay", identity)
        self.observation_id = observation_id
        self.evidence_id = evidence_id
        self.content_hash = content_hash
        self.matches = matches
        self.schema_version = schema_version

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "content_hash": self.content_hash,
            "evidence_id": self.evidence_id,
            "matches": self.matches,
            "observation_id": self.observation_id,
            "receipt_id": self.receipt_id,
            "schema_version": self.schema_version,
        }


class JsonSolanaObservationStore:
    """Atomic, content-addressed persistence for Solana observation payloads."""

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._payloads: dict[str, EvidencePayload] = {}
        self._load()

    def append(self, payload: EvidencePayload) -> str:
        if not isinstance(payload, EvidencePayload):
            raise TypeError("payload must be an EvidencePayload")
        if payload.evidence_type != "solana_chain_observation":
            raise ValueError("payload evidence_type must be solana_chain_observation")
        SolanaObservationParser.from_payload(payload)
        identity = payload.get_canonical_id()
        existing = self._payloads.get(identity)
        if existing is not None:
            if existing != payload:
                raise RuntimeError("Solana observation identity collision")
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

    def replay(
        self,
        observation: SolanaChainObservation,
    ) -> SolanaObservationStoreReplayReceipt:
        if not isinstance(observation, SolanaChainObservation):
            raise TypeError("observation must be a SolanaChainObservation")
        expected = SolanaObservationParser.from_observation(observation).payload
        evidence_id = expected.get_canonical_id()
        retained = self._payloads.get(evidence_id)
        if retained is None:
            raise ValueError("persisted Solana observation is missing from store")
        if retained.canonical_dict() != expected.canonical_dict():
            raise ValueError("persisted Solana observation does not match source")
        SolanaObservationParser.from_payload(retained)
        return SolanaObservationStoreReplayReceipt(
            observation_id=observation.observation_id,
            evidence_id=evidence_id,
            content_hash=_digest(retained.canonical_dict()),
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
            raise ValueError("Solana observation store is not valid JSON") from exc
        if not isinstance(document, dict) or set(document) != {
            "content_hash", "payloads", "schema_version"
        }:
            raise ValueError("Solana observation store keys do not match schema")
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError("unsupported Solana observation store schema_version")
        records = document["payloads"]
        if not isinstance(records, list) or _digest(records) != document["content_hash"]:
            raise ValueError("Solana observation store content hash mismatch")
        if canonical_json(document) != raw:
            raise ValueError("Solana observation store is not canonical JSON")
        loaded: dict[str, EvidencePayload] = {}
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("invalid Solana observation payload")
            try:
                payload = EvidencePayload(
                    source_id=record["source_id"],
                    evidence_type=record["evidence_type"],
                    timestamp=record["timestamp"],
                    data=record["data"],
                    metadata=record["metadata"],
                )
                SolanaObservationParser.from_payload(payload)
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("invalid Solana observation payload") from exc
            identity = payload.get_canonical_id()
            if identity in loaded:
                raise ValueError("duplicate Solana observation ID")
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


__all__ = [
    "JsonSolanaObservationStore",
    "SolanaObservationStoreReplayReceipt",
]
