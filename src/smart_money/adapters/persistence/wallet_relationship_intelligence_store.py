from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from pathlib import Path

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.wallet_relationship_intelligence import (
    WalletRelationshipIntelligence,
)
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "wallet_relationship_intelligence_store.v1"


class JsonWalletRelationshipIntelligenceStore:
    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._models: dict[str, WalletRelationshipIntelligence] = {}
        self._load_existing()

    def append(self, model: WalletRelationshipIntelligence) -> str:
        if not isinstance(model, WalletRelationshipIntelligence):
            raise TypeError("model must be WalletRelationshipIntelligence")
        existing = self._models.get(model.intelligence_id)
        if existing is not None:
            if existing != model:
                raise RuntimeError("wallet relationship intelligence identity collision")
            return model.intelligence_id
        candidate = dict(self._models)
        candidate[model.intelligence_id] = model
        self._persist(tuple(candidate.values()))
        self._models = candidate
        return model.intelligence_id

    def get(self, intelligence_id: str) -> WalletRelationshipIntelligence | None:
        return self._models.get(intelligence_id)

    def iter_models(self) -> Iterator[WalletRelationshipIntelligence]:
        return iter(tuple(self._models.values()))

    @property
    def model_count(self) -> int:
        return len(self._models)

    def _load_existing(self) -> None:
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        source = self._file_path if self._file_path.is_file() else temporary
        if not source.is_file():
            return
        loaded = self._load_path(source)
        if source == temporary:
            atomic_replace(temporary, self._file_path)
        self._models = loaded

    def _load_path(self, path: Path) -> dict[str, WalletRelationshipIntelligence]:
        raw = path.read_text(encoding="utf-8")
        document = json.loads(raw)
        if not isinstance(document, dict) or document.get("schema_version") != _SCHEMA_VERSION:
            raise ValueError("invalid wallet relationship intelligence store schema")
        records = document.get("models")
        if not isinstance(records, list) or document.get("content_hash") != _hash(records):
            raise ValueError("wallet relationship intelligence store content hash mismatch")
        if canonical_json(document) != raw:
            raise ValueError("wallet relationship intelligence store is not canonical JSON")
        loaded: dict[str, WalletRelationshipIntelligence] = {}
        for record in records:
            model = WalletRelationshipIntelligence(
                cluster_id=record["cluster_id"],
                intelligence_id=record["intelligence_id"],
                relationship_count=record["relationship_count"],
                relationship_ids=tuple(record["relationship_ids"]),
                schema_version=record["schema_version"],
                wallets=tuple(record["wallets"]),
            )
            if model.intelligence_id in loaded:
                raise ValueError("duplicate wallet relationship intelligence model")
            loaded[model.intelligence_id] = model
        return loaded

    def _persist(self, models: tuple[WalletRelationshipIntelligence, ...]) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        records = [model.canonical_dict() for model in models]
        document = {
            "content_hash": _hash(records),
            "models": records,
            "schema_version": _SCHEMA_VERSION,
        }
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)


def _hash(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


__all__ = ["JsonWalletRelationshipIntelligenceStore"]
