from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from smart_money.application._validation import (
    StableCollectionSnapshot,
    assert_stable_collection_snapshot,
    require_count,
    require_sha256,
    require_text,
    take_stable_collection_snapshot,
)


class _Store:
    def __init__(self) -> None:
        self.items = ("a", "b")

    @property
    def content_hash(self) -> str:
        return "a" * 64

    @property
    def count(self) -> int:
        return len(self.items)

    def iter_items(self) -> tuple[str, ...]:
        return self.items

    def get(self, item_id: str) -> str | None:
        return item_id if item_id in self.items else None


def test_validation_primitives_normalize_and_reject_invalid_values() -> None:
    assert require_text("  value ", "value") == "value"
    assert require_sha256("a" * 64, "digest") == "a" * 64
    assert require_count(2, "count") == 2
    with pytest.raises(ValueError):
        require_text(" ", "value")
    with pytest.raises(ValueError):
        require_sha256("A" * 64, "digest")
    with pytest.raises(TypeError):
        require_count(True, "count")


def test_stable_snapshot_is_immutable_and_consistent() -> None:
    store = _Store()
    snapshot = take_stable_collection_snapshot(
        name="store",
        get_content_hash=lambda: store.content_hash,
        get_count=lambda: store.count,
        iterate=store.iter_items,
        identity=lambda item: item,
        lookup=store.get,
    )
    assert snapshot == StableCollectionSnapshot("a" * 64, 2, ("a", "b"))
    with pytest.raises(FrozenInstanceError):
        snapshot.count = 3  # type: ignore[misc]
    assert_stable_collection_snapshot(
        snapshot,
        name="store",
        get_content_hash=lambda: store.content_hash,
        get_count=lambda: store.count,
    )


def test_stable_snapshot_fails_closed_on_mutation() -> None:
    store = _Store()
    snapshot = take_stable_collection_snapshot(
        name="store",
        get_content_hash=lambda: store.content_hash,
        get_count=lambda: store.count,
        iterate=store.iter_items,
        identity=lambda item: item,
        lookup=store.get,
    )
    store.items = ("a",)
    with pytest.raises(RuntimeError, match="changed during snapshot"):
        assert_stable_collection_snapshot(
            snapshot,
            name="store",
            get_content_hash=lambda: store.content_hash,
            get_count=lambda: store.count,
        )
