"""Generic single-value JSON store.

Replaces the boilerplate duplicated across ~15 domain-specific stores
that each hold a single receipt/profile/checkpoint at a time.

See :mod:`generic_collection_store` for the collection variant.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.core.serialization import canonical_json

# ---------------------------------------------------------------------------
# Value protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class StoredValue(Protocol):
    """Minimal interface for a single storable value."""

    def canonical_dict(self) -> dict[str, Any]: ...


# ---------------------------------------------------------------------------
# Value-store manifest
# ---------------------------------------------------------------------------

def _default_parse(raw: dict[str, Any], **_kw: Any) -> Any:
    return raw


@dataclass(frozen=True, slots=True)
class ValueStoreManifest:
    """Configuration that varies per domain value-store."""

    schema_version: str
    value_key: str = "value"
    id_field: str | None = None  # None = no collision check

    parse: Callable[[dict[str, Any]], Any] = _default_parse
    verify_canonical: bool = False
    content_hash: bool = False
    immutable: bool = False
    collision_message: str | None = None


# ---------------------------------------------------------------------------
# Generic value store
# ---------------------------------------------------------------------------

class GenericValueStore:
    """Single-value, atomic JSON store.

    Drop-in replacement for stores that hold one receipt/profile at a
    time: ``save(value) -> id / load() -> value | None``.
    """

    __slots__ = ("_file_path", "_manifest", "_value")

    def __init__(
        self,
        file_path: str | os.PathLike[str],
        manifest: ValueStoreManifest,
    ) -> None:
        self._file_path = Path(file_path)
        self._manifest = manifest
        self._value: StoredValue | None = None
        self._load_existing()

    # -- public API ---------------------------------------------------------

    def save(self, value: StoredValue) -> str:
        m = self._manifest
        if m.immutable and self._value is not None and canonical_json(self._value.canonical_dict()) != canonical_json(value.canonical_dict()):
            raise RuntimeError(m.collision_message or "immutable value overwrite rejected")
        value_id: str | None = (
            getattr(value, m.id_field) if m.id_field else None
        )
        if m.id_field and self._value is not None:
            existing_id = getattr(self._value, m.id_field)
            if existing_id != value_id:
                raise RuntimeError(
                    f"{type(value).__name__} identity collision"
                )

        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        document: dict[str, Any] = {
            "schema_version": m.schema_version,
            m.value_key: value.canonical_dict(),
        }
        if m.content_hash:
            document["content_hash"] = hashlib.sha256(canonical_json(document[m.value_key]).encode("utf-8")).hexdigest()
        temporary = self._temporary_path()
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)
        self._value = value
        return value_id or ""

    def load(self) -> StoredValue | None:
        return self._value

    # -- persistence --------------------------------------------------------

    def _load_existing(self) -> None:
        if not self._file_path.is_file():
            return
        m = self._manifest
        try:
            raw = self._file_path.read_text(encoding="utf-8")
            document: Any = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"{m.schema_version}: not valid JSON"
            ) from exc

        if not isinstance(document, dict):
            raise ValueError(f"{m.schema_version}: root must be an object")  # noqa: TRY004 - persisted-format error compatibility

        if document.get("schema_version") != m.schema_version:
            raise ValueError(
                f"unsupported schema_version: "
                f"{document.get('schema_version')}"
            )

        raw_value = document.get(m.value_key)
        if m.content_hash:
            if set(document) != {"schema_version", m.value_key, "content_hash"} or not isinstance(raw_value, dict):
                raise ValueError("store keys do not match hashed schema")
            expected = hashlib.sha256(canonical_json(raw_value).encode("utf-8")).hexdigest()
            if document["content_hash"] != expected:
                raise ValueError("store content hash mismatch")
        if raw_value is None:
            self._value = None
            return

        if not isinstance(raw_value, dict):
            raise ValueError(f"{m.value_key} must be an object")  # noqa: TRY004 - persisted-format error compatibility

        self._value = m.parse(raw_value)

        if m.verify_canonical and canonical_json(document) != raw:
            raise ValueError("store is not canonical JSON")

    def _temporary_path(self) -> Path:
        return self._file_path.with_name(f"{self._file_path.name}.tmp")


__all__ = [
    "GenericValueStore",
    "StoredValue",
    "ValueStoreManifest",
]
