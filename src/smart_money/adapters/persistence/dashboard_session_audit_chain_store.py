from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.dashboard_session_audit_chain import (
    DashboardSessionAuditChain,
    DashboardSessionAuditEntry,
)
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "dashboard_session_audit_chain_store.v1"


class JsonDashboardSessionAuditChainStore:
    """Atomic persistence for one canonical session audit chain."""

    __slots__ = ("_file_path", "_chain")

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._chain: DashboardSessionAuditChain | None = None
        self._load()

    def save(self, chain: DashboardSessionAuditChain) -> str:
        if not isinstance(chain, DashboardSessionAuditChain):
            raise TypeError("chain must be a DashboardSessionAuditChain")
        if self._chain is not None and self._chain != chain:
            raise RuntimeError("session audit chain overwrite rejected")
        document = {
            "chain": chain.canonical_dict(),
            "content_hash": _digest(chain.canonical_dict()),
            "schema_version": _SCHEMA_VERSION,
        }
        if self._file_path.parent != Path("."):
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)
        self._chain = chain
        return chain.chain_id

    def load(self) -> DashboardSessionAuditChain | None:
        return self._chain

    def _load(self) -> None:
        if not self._file_path.is_file():
            return
        try:
            document = json.loads(self._file_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("session audit chain is not valid JSON") from exc
        if not isinstance(document, dict) or set(document) != {
            "chain",
            "content_hash",
            "schema_version",
        }:
            raise ValueError("session audit chain keys do not match schema")
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError("unsupported session audit chain store schema_version")
        chain_data = document["chain"]
        if not isinstance(chain_data, dict) or _digest(chain_data) != document[
            "content_hash"
        ]:
            raise ValueError("session audit chain content hash mismatch")
        if canonical_json(document) != self._file_path.read_text(encoding="utf-8"):
            raise ValueError("session audit chain is not canonical JSON")
        try:
            entries = tuple(
                DashboardSessionAuditEntry(
                    entry_kind=item["entry_kind"],
                    entry_id=item["entry_id"],
                    parent_id=item["parent_id"],
                    schema_version=item["schema_version"],
                )
                for item in chain_data["entries"]
            )
            self._chain = DashboardSessionAuditChain(
                entries=entries,
                chain_hash=chain_data["chain_hash"],
                schema_version=chain_data["schema_version"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid session audit chain") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


__all__ = ["JsonDashboardSessionAuditChainStore"]
