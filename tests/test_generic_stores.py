"""Behavior contract tests for GenericCollectionStore and GenericValueStore.

These tests define the exact behavioral contract that every domain store
must satisfy.  When a domain store is migrated to the generic base, these
same tests apply without modification.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from smart_money.adapters.persistence.generic_collection_store import (
    GenericCollectionStore,
    StoreManifest,
)
from smart_money.adapters.persistence.generic_value_store import (
    GenericValueStore,
    ValueStoreManifest,
)
from smart_money.core.serialization import canonical_json


# ---------------------------------------------------------------------------
# Minimal receipt types for testing
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class FakeReceipt:
    receipt_id: str
    value: str
    schema_version: str = "fake.v1"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "schema_version": self.schema_version,
            "value": self.value,
        }


@dataclass(frozen=True, slots=True)
class FakeSingleValue:
    profile_id: str
    name: str
    schema_version: str = "fake_single.v1"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "schema_version": self.schema_version,
        }


def _parse_receipt(raw: dict[str, Any]) -> FakeReceipt:
    return FakeReceipt(
        receipt_id=raw["receipt_id"],
        value=raw["value"],
        schema_version=raw.get("schema_version", "fake.v1"),
    )


def _parse_value(raw: dict[str, Any]) -> FakeSingleValue:
    return FakeSingleValue(
        profile_id=raw["profile_id"],
        name=raw["name"],
        schema_version=raw.get("schema_version", "fake_single.v1"),
    )


def _sha256_hex(data: list[dict[str, Any]]) -> str:
    return hashlib.sha256(
        canonical_json(data).encode("utf-8")
    ).hexdigest()


COLLECTION_MANIFEST = StoreManifest(
    schema_version="fake.v1",
    collection_key="receipts",
    id_field="receipt_id",
    parse=_parse_receipt,
    verify_canonical=True,
    document_keys=frozenset({"schema_version", "content_hash", "receipts"}),
)

COLLECTION_MANIFEST_NO_VERIFY = StoreManifest(
    schema_version="fake_noverify.v1",
    collection_key="receipts",
    id_field="receipt_id",
    parse=_parse_receipt,
    verify_canonical=False,
)

VALUE_MANIFEST = ValueStoreManifest(
    schema_version="fake_single.v1",
    value_key="profile",
    id_field="profile_id",
    parse=_parse_value,
    verify_canonical=True,
)


# ===================================================================
# COLLECTION STORE — behavior contract
# ===================================================================


@pytest.fixture
def td() -> Path:
    d = Path(tempfile.mkdtemp(prefix="test_gs_"))
    yield d
    import shutil
    shutil.rmtree(d, ignore_errors=True)


class TestCollectionStoreAppend:
    """append() stores an item and returns its ID."""

    def test_append_returns_id(self, td: Path) -> None:
        store = GenericCollectionStore(
            td / "a.json", COLLECTION_MANIFEST
        )
        r = FakeReceipt(receipt_id="r1", value="hello")
        assert store.append(r) == "r1"
        assert store.count == 1

    def test_append_idempotent(self, td: Path) -> None:
        store = GenericCollectionStore(
            td / "a.json", COLLECTION_MANIFEST
        )
        r = FakeReceipt(receipt_id="r1", value="hello")
        assert store.append(r) == "r1"
        assert store.append(r) == "r1"
        assert store.count == 1

    def test_append_collision_raises(self, td: Path) -> None:
        store = GenericCollectionStore(
            td / "a.json", COLLECTION_MANIFEST
        )
        store.append(FakeReceipt(receipt_id="r1", value="hello"))
        with pytest.raises(RuntimeError, match="identity collision"):
            store.append(FakeReceipt(receipt_id="r1", value="changed"))


class TestCollectionStoreGet:
    """get() retrieves by ID or returns None."""

    def test_get_existing(self, td: Path) -> None:
        store = GenericCollectionStore(
            td / "a.json", COLLECTION_MANIFEST
        )
        r = FakeReceipt(receipt_id="r1", value="hello")
        store.append(r)
        assert store.get("r1") == r

    def test_get_missing(self, td: Path) -> None:
        store = GenericCollectionStore(
            td / "a.json", COLLECTION_MANIFEST
        )
        assert store.get("nope") is None


class TestCollectionStoreIteration:
    """iter_items() yields all stored items."""

    def test_iter_yields_all(self, td: Path) -> None:
        store = GenericCollectionStore(
            td / "a.json", COLLECTION_MANIFEST
        )
        r1 = FakeReceipt(receipt_id="r1", value="a")
        r2 = FakeReceipt(receipt_id="r2", value="b")
        store.append(r1)
        store.append(r2)
        items = list(store.iter_items())
        assert len(items) == 2
        assert r1 in items and r2 in items


class TestCollectionStorePersistence:
    """Items survive load-from-disk."""

    def test_reload_persists_items(self, td: Path) -> None:
        path = td / "a.json"
        r1 = FakeReceipt(receipt_id="r1", value="hello")
        r2 = FakeReceipt(receipt_id="r2", value="world")

        store1 = GenericCollectionStore(path, COLLECTION_MANIFEST)
        store1.append(r1)
        store1.append(r2)

        store2 = GenericCollectionStore(path, COLLECTION_MANIFEST)
        assert store2.count == 2
        assert store2.get("r1") == r1
        assert store2.get("r2") == r2

    def test_reload_empty_file(self, td: Path) -> None:
        path = td / "a.json"
        store = GenericCollectionStore(path, COLLECTION_MANIFEST)
        assert store.count == 0

    def test_reload_from_tmp_file(self, td: Path) -> None:
        """If .tmp exists but main file doesn't, recover from .tmp."""
        path = td / "a.json"
        tmp = path.with_name("a.json.tmp")
        r = FakeReceipt(receipt_id="r1", value="recovered")
        records = [r.canonical_dict()]
        doc = {
            "schema_version": "fake.v1",
            "content_hash": _sha256_hex(records),
            "receipts": records,
        }
        tmp.write_text(canonical_json(doc), encoding="utf-8")

        store = GenericCollectionStore(path, COLLECTION_MANIFEST)
        assert store.count == 1
        assert store.get("r1") == r
        assert path.is_file()
        assert not tmp.exists()


class TestCollectionStoreVerification:
    """Content-hash and canonical-JSON verification."""

    def test_hash_mismatch_raises(self, td: Path) -> None:
        path = td / "a.json"
        r = FakeReceipt(receipt_id="r1", value="hello")
        records = [r.canonical_dict()]
        doc = {
            "schema_version": "fake.v1",
            "content_hash": "0" * 64,  # wrong hash
            "receipts": records,
        }
        path.write_text(canonical_json(doc), encoding="utf-8")

        with pytest.raises(ValueError, match="content hash mismatch"):
            GenericCollectionStore(path, COLLECTION_MANIFEST)

    def test_canonical_check_catches_non_canonical(self, td: Path) -> None:
        path = td / "a.json"
        r = FakeReceipt(receipt_id="r1", value="hello")
        records = [r.canonical_dict()]
        doc = {
            "schema_version": "fake.v1",
            "content_hash": _sha256_hex(records),
            "receipts": records,
        }
        raw = json.dumps(doc, indent=2)
        path.write_text(raw, encoding="utf-8")

        with pytest.raises(ValueError, match="canonical JSON"):
            GenericCollectionStore(path, COLLECTION_MANIFEST)

    def test_no_canonical_check_allows_non_canonical(self, td: Path) -> None:
        path = td / "a.json"
        r = FakeReceipt(receipt_id="r1", value="hello")
        records = [r.canonical_dict()]
        doc = {
            "schema_version": "fake_noverify.v1",
            "content_hash": _sha256_hex(records),
            "receipts": records,
        }
        raw = json.dumps(doc, indent=2)
        path.write_text(raw, encoding="utf-8")

        store = GenericCollectionStore(path, COLLECTION_MANIFEST_NO_VERIFY)
        assert store.count == 1

    def test_schema_version_mismatch_raises(self, td: Path) -> None:
        path = td / "a.json"
        doc = {
            "schema_version": "wrong.v1",
            "content_hash": _sha256_hex([]),
            "receipts": [],
        }
        path.write_text(canonical_json(doc), encoding="utf-8")

        with pytest.raises(ValueError, match="unsupported schema_version"):
            GenericCollectionStore(path, COLLECTION_MANIFEST)

    def test_content_hash_property(self, td: Path) -> None:
        store = GenericCollectionStore(
            td / "a.json", COLLECTION_MANIFEST
        )
        r1 = FakeReceipt(receipt_id="r1", value="a")
        store.append(r1)
        h = store.content_hash
        assert isinstance(h, str)
        assert len(h) == 64
        assert store.content_hash == h


# ===================================================================
# VALUE STORE — behavior contract
# ===================================================================


class TestValueStoreSave:
    """save() stores a value and returns its ID."""

    def test_save_returns_id(self, td: Path) -> None:
        store = GenericValueStore(
            td / "v.json", VALUE_MANIFEST
        )
        v = FakeSingleValue(profile_id="p1", name="alice")
        result = store.save(v)
        assert result == "p1"
        assert store.load() == v

    def test_save_overwrite(self, td: Path) -> None:
        store = GenericValueStore(
            td / "v.json", VALUE_MANIFEST
        )
        v1 = FakeSingleValue(profile_id="p1", name="alice")
        v2 = FakeSingleValue(profile_id="p1", name="alice_v2")
        store.save(v1)
        store.save(v2)  # same ID, allowed
        assert store.load() == v2


class TestValueStoreLoad:
    """load() returns the stored value or None."""

    def test_load_empty(self, td: Path) -> None:
        store = GenericValueStore(
            td / "v.json", VALUE_MANIFEST
        )
        assert store.load() is None

    def test_reload_persists(self, td: Path) -> None:
        path = td / "v.json"
        v = FakeSingleValue(profile_id="p1", name="alice")

        store1 = GenericValueStore(path, VALUE_MANIFEST)
        store1.save(v)

        store2 = GenericValueStore(path, VALUE_MANIFEST)
        assert store2.load() == v


class TestValueStoreVerification:
    """Schema version and canonical checks."""

    def test_schema_version_mismatch(self, td: Path) -> None:
        path = td / "v.json"
        doc = {"schema_version": "wrong.v1", "profile": {"x": 1}}
        path.write_text(canonical_json(doc), encoding="utf-8")

        with pytest.raises(ValueError, match="unsupported schema_version"):
            GenericValueStore(path, VALUE_MANIFEST)

    def test_canonical_check(self, td: Path) -> None:
        path = td / "v.json"
        v = FakeSingleValue(profile_id="p1", name="alice")
        doc = {"schema_version": "fake_single.v1", "profile": v.canonical_dict()}
        path.write_text(json.dumps(doc, indent=2), encoding="utf-8")

        with pytest.raises(ValueError, match="canonical JSON"):
            GenericValueStore(path, VALUE_MANIFEST)
