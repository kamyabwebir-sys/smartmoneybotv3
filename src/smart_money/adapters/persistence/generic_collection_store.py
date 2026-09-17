"""Generic append-only JSON collection store.

Replaces the boilerplate duplicated across ~50 domain-specific stores.
Each store that holds a collection of receipts/models/items can inherit
from :class:`GenericCollectionStore` and supply only a
:class:`StoreManifest` plus the domain receipt type.

The manifest defines the thin slice that varies between stores: schema
version, key name inside the JSON document, how to reconstruct a receipt
from a raw dict, and which fields identify it.  Everything else — load,
persist, collision detection, atomic writes, content-hash verification —
lives here and never needs rewriting.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.core.serialization import canonical_json


# ---------------------------------------------------------------------------
# Receipt protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class Receipt(Protocol):
    """Minimal interface for a storable receipt object."""

    def canonical_dict(self) -> dict[str, Any]: ...


# ---------------------------------------------------------------------------
# Store manifest — the only thing a domain store needs to supply
# ---------------------------------------------------------------------------

def _default_hash(data: list[dict[str, Any]]) -> str:
    return hashlib.sha256(
        canonical_json(data).encode("utf-8")
    ).hexdigest()


def _default_parse(raw: dict[str, Any], **_kw: Any) -> Any:
    """Fallback: pass-through raw dict (for stores that do their own parse)."""
    return raw


@dataclass(frozen=True, slots=True)
class StoreManifest:
    """Configuration that varies per domain store.

    ``parse`` reconstructs a receipt from a raw JSON dict.
    """

    schema_version: str
    collection_key: str = "receipts"
    id_field: str = "receipt_id"

    # -- parsing ------------------------------------------------------------
    parse: Callable[[dict[str, Any]], Any] = _default_parse

    # -- verification -------------------------------------------------------
    compute_hash: Callable[[list[dict[str, Any]]], str] = _default_hash
    compare_hash: Callable[[str, str], bool] = lambda a, b: a == b
    verify_canonical: bool = False

    # -- document structure -------------------------------------------------
    document_keys: frozenset[str] | None = None  # None = do not check


# ---------------------------------------------------------------------------
# Generic collection store
# ---------------------------------------------------------------------------

class GenericCollectionStore:
    """Append-only, single-writer, atomic JSON collection store.

    Drop-in replacement for the ~50 domain stores that follow the
    pattern: ``__init__(file_path) -> append/reget/iter/count``.

    Subclass or instantiate directly with a :class:`StoreManifest`.
    """

    __slots__ = ("_file_path", "_manifest", "_items")

    def __init__(
        self,
        file_path: str | os.PathLike[str],
        manifest: StoreManifest,
    ) -> None:
        self._file_path = Path(file_path)
        self._manifest = manifest
        self._items: dict[str, R] = {}
        self._load_existing()

    # -- public API ---------------------------------------------------------

    def append(self, item: R) -> str:
        item_id = getattr(item, self._manifest.id_field)
        existing = self._items.get(item_id)
        if existing is not None:
            if existing != item:
                raise RuntimeError(
                    f"{type(item).__name__} identity collision"
                )
            return item_id

        candidate = dict(self._items)
        candidate[item_id] = item
        self._persist(tuple(candidate.values()))
        self._items = candidate
        return item_id

    def get(self, item_id: str) -> R | None:
        return self._items.get(item_id)

    def iter_items(self) -> Iterator[R]:
        return iter(tuple(self._items.values()))

    @property
    def count(self) -> int:
        return len(self._items)

    @property
    def content_hash(self) -> str:
        return self._manifest.compute_hash(
            [item.canonical_dict() for item in self._items.values()]
        )

    # -- persistence --------------------------------------------------------

    def _persist(self, items: tuple[R, ...]) -> None:
        if self._file_path.parent != Path("."):
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
        records = [item.canonical_dict() for item in items]
        document: dict[str, Any] = {
            "schema_version": self._manifest.schema_version,
            "content_hash": self._manifest.compute_hash(records),
            self._manifest.collection_key: records,
        }
        temporary = self._temporary_path()
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)

    def _load_existing(self) -> None:
        temporary = self._temporary_path()
        recovering = False
        if self._file_path.is_file():
            source = self._file_path
        elif temporary.is_file():
            source = temporary
            recovering = True
        else:
            return

        try:
            loaded = self._load_from_path(source)
        except ValueError as exc:
            if recovering:
                raise ValueError(
                    f"temporary recovery failed: {temporary}"
                ) from exc
            raise
        if recovering:
            atomic_replace(temporary, self._file_path)
        self._items = loaded

    def _load_from_path(self, path: Path) -> dict[str, R]:
        m = self._manifest
        try:
            raw = path.read_text(encoding="utf-8")
            document: Any = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"{m.schema_version}: not valid JSON"
            ) from exc

        if not isinstance(document, dict):
            raise ValueError(f"{m.schema_version}: root must be an object")

        if m.document_keys is not None and set(document) != m.document_keys:
            raise ValueError(
                f"{m.schema_version}: document keys do not match schema"
            )

        if document.get("schema_version") != m.schema_version:
            raise ValueError(
                f"unsupported schema_version: "
                f"{document.get('schema_version')}"
            )

        records = document.get(m.collection_key)
        if not isinstance(records, list):
            raise ValueError(
                f"{m.collection_key} must be a list"
            )

        content_hash = document.get("content_hash")
        if content_hash is not None:
            if not isinstance(content_hash, str):
                raise ValueError("content_hash must be a string")
            expected = m.compute_hash(records)
            if not m.compare_hash(content_hash, expected):
                raise ValueError("content hash mismatch")

        if m.verify_canonical and canonical_json(document) != raw:
            raise ValueError("store is not canonical JSON")

        loaded: dict[str, R] = {}
        for record in records:
            if not isinstance(record, dict):
                raise ValueError(
                    f"each {m.collection_key} entry must be an object"
                )
            receipt = m.parse(record)
            receipt_id = getattr(receipt, m.id_field)
            if receipt_id in loaded:
                raise ValueError(
                    f"duplicate {m.id_field}: {receipt_id}"
                )
            loaded[receipt_id] = receipt
        return loaded

    def _temporary_path(self) -> Path:
        return self._file_path.with_name(f"{self._file_path.name}.tmp")


__all__ = [
    "GenericCollectionStore",
    "Receipt",
    "StoreManifest",
]
