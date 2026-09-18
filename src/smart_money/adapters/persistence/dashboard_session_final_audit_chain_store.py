from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from pathlib import Path

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.dashboard_session_audit_chain import (
    DashboardSessionAuditEntry,
)
from smart_money.application.dashboard_session_final_audit_chain import (
    DashboardSessionFinalAuditChain,
)
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "dashboard_session_final_audit_chain_store.v1"


class JsonDashboardSessionFinalAuditChainStore:
    """Atomic, append-only persistence for integrated final audit chains."""

    __slots__ = ("_file_path", "_chains")

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._chains: dict[str, DashboardSessionFinalAuditChain] = {}
        self._load()

    def append(self, chain: DashboardSessionFinalAuditChain) -> str:
        if not isinstance(chain, DashboardSessionFinalAuditChain):
            raise TypeError(
                "chain must be a DashboardSessionFinalAuditChain"
            )
        existing = self._chains.get(chain.chain_id)
        if existing is not None:
            if existing != chain:
                raise RuntimeError("session final audit chain identity collision")
            return chain.chain_id
        candidate = dict(self._chains)
        candidate[chain.chain_id] = chain
        self._persist(tuple(candidate.values()))
        self._chains = candidate
        return chain.chain_id

    def get(self, chain_id: str) -> DashboardSessionFinalAuditChain | None:
        return self._chains.get(chain_id)

    def iter_chains(self) -> Iterator[DashboardSessionFinalAuditChain]:
        return iter(tuple(self._chains.values()))

    @property
    def chain_count(self) -> int:
        return len(self._chains)

    @property
    def content_hash(self) -> str:
        return _digest([item.canonical_dict() for item in self._chains.values()])

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
            document = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                "session final audit chain store is not valid JSON"
            ) from exc
        if not isinstance(document, dict) or set(document) != {
            "chains",
            "content_hash",
            "schema_version",
        }:
            raise ValueError(
                "session final audit chain store keys do not match schema"
            )
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError(
                "unsupported session final audit chain store schema_version"
            )
        records = document["chains"]
        if not isinstance(records, list) or _digest(records) != document[
            "content_hash"
        ]:
            raise ValueError(
                "session final audit chain store content hash mismatch"
            )
        if canonical_json(document) != raw:
            raise ValueError(
                "session final audit chain store is not canonical JSON"
            )
        loaded: dict[str, DashboardSessionFinalAuditChain] = {}
        for record in records:
            try:
                entries = tuple(
                    DashboardSessionAuditEntry(
                        entry_kind=item["entry_kind"],
                        entry_id=item["entry_id"],
                        parent_id=item["parent_id"],
                        schema_version=item["schema_version"],
                    )
                    for item in record["entries"]
                )
                chain = DashboardSessionFinalAuditChain(
                    entries=entries,
                    chain_hash=record["chain_hash"],
                    schema_version=record["schema_version"],
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("invalid session final audit chain") from exc
            if chain.chain_id in loaded:
                raise ValueError("duplicate session final audit chain ID")
            loaded[chain.chain_id] = chain
        if recovering:
            atomic_replace(temporary, self._file_path)
        self._chains = loaded

    def _persist(
        self,
        chains: tuple[DashboardSessionFinalAuditChain, ...],
    ) -> None:
        if self._file_path.parent != Path("."):
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
        records = [item.canonical_dict() for item in chains]
        document = {
            "chains": records,
            "content_hash": _digest(records),
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


__all__ = ["JsonDashboardSessionFinalAuditChainStore"]
