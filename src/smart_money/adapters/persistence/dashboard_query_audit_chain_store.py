from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.dashboard_query_audit_chain import (
    DashboardQueryAuditChain,
)
from smart_money.application.dashboard_query_replay_verifier import (
    DashboardQueryReplayReceipt,
)
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "dashboard_query_audit_chain_store.v1"
_DOCUMENT_KEYS = frozenset({"chain", "content_hash", "schema_version"})


class JsonDashboardQueryAuditChainStore:
    """Atomic, canonical persistence for one dashboard audit chain."""

    __slots__ = ("_file_path", "_chain")

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._chain: DashboardQueryAuditChain | None = None
        self._load()

    def save(self, chain: DashboardQueryAuditChain) -> str:
        if not isinstance(chain, DashboardQueryAuditChain):
            raise TypeError("chain must be a DashboardQueryAuditChain")
        if self._chain is not None and self._chain.chain_id != chain.chain_id:
            raise RuntimeError("audit chain identity collision")
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

    def load(self) -> DashboardQueryAuditChain | None:
        return self._chain

    @property
    def chain_id(self) -> str | None:
        return None if self._chain is None else self._chain.chain_id

    def _load(self) -> None:
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        if self._file_path.is_file():
            source, recovering = self._file_path, False
        elif temporary.is_file():
            source, recovering = temporary, True
        else:
            return
        chain = self._load_path(source)
        if recovering:
            atomic_replace(temporary, self._file_path)
        self._chain = chain

    def _load_path(self, path: Path) -> DashboardQueryAuditChain:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"dashboard audit chain is not valid JSON: {path}") from exc
        if not isinstance(document, dict) or set(document) != _DOCUMENT_KEYS:
            raise ValueError("dashboard audit chain keys do not match schema")
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError("unsupported dashboard audit chain store schema_version")
        chain_data = document["chain"]
        if not isinstance(chain_data, dict):
            raise ValueError("dashboard audit chain payload must be an object")
        content_hash = document["content_hash"]
        if not isinstance(content_hash, str) or len(content_hash) != 64:
            raise ValueError("content_hash must be a SHA-256 hex digest")
        if _digest(chain_data) != content_hash:
            raise ValueError("dashboard audit chain content hash mismatch")
        if canonical_json(document) != path.read_text(encoding="utf-8"):
            raise ValueError("dashboard audit chain is not canonical JSON")
        try:
            records = chain_data["receipts"]
            receipts = tuple(
                DashboardQueryReplayReceipt(
                    query_id=record["query_id"],
                    expected_receipt_id=record["expected_receipt_id"],
                    actual_receipt_id=record["actual_receipt_id"],
                    matches=record["matches"],
                    mismatches=tuple(record["mismatches"]),
                    schema_version=record["schema_version"],
                )
                for record in records
            )
            return DashboardQueryAuditChain(
                receipts=receipts,
                chain_hash=chain_data["chain_hash"],
                schema_version=chain_data["schema_version"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid dashboard audit chain") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


__all__ = ["JsonDashboardQueryAuditChainStore"]
