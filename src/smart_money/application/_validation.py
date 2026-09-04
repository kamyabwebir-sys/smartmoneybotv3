from __future__ import annotations

import hmac
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Generic, TypeVar

_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_ItemT = TypeVar("_ItemT")


def require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def require_sha256(value: object, field_name: str) -> str:
    digest = require_text(value, field_name)
    if _SHA256_PATTERN.fullmatch(digest) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 hex digest")
    return digest


def require_count(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


@dataclass(frozen=True, slots=True)
class StableCollectionSnapshot(Generic[_ItemT]):
    content_hash: str
    count: int
    items: tuple[_ItemT, ...]


def take_stable_collection_snapshot(
    *,
    name: str,
    get_content_hash: Callable[[], object],
    get_count: Callable[[], object],
    iterate: Callable[[], Iterable[_ItemT]],
    identity: Callable[[_ItemT], str],
    lookup: Callable[[str], _ItemT | None],
    item_type: type[object] | None = None,
) -> StableCollectionSnapshot[_ItemT]:
    """Capture and verify one deterministic content-addressed collection."""
    content_hash = require_sha256(
        get_content_hash(),
        f"{name}.content_hash",
    )
    count = require_count(get_count(), f"{name}.count")
    items = tuple(iterate())
    if len(items) != count:
        raise RuntimeError(f"{name} count changed during snapshot")
    if item_type is not None and not all(
        isinstance(item, item_type) for item in items
    ):
        raise RuntimeError(f"{name} contains an invalid item type")
    identities = tuple(identity(item) for item in items)
    if len(set(identities)) != count:
        raise RuntimeError(f"{name} snapshot contains duplicate identities")
    for item_id, item in zip(identities, items, strict=True):
        if lookup(item_id) != item:
            raise RuntimeError(f"{name} lookup disagrees with iteration")
    snapshot = StableCollectionSnapshot(content_hash, count, items)
    assert_stable_collection_snapshot(
        snapshot,
        name=name,
        get_content_hash=get_content_hash,
        get_count=get_count,
    )
    return snapshot


def assert_stable_collection_snapshot(
    snapshot: StableCollectionSnapshot[object],
    *,
    name: str,
    get_content_hash: Callable[[], object],
    get_count: Callable[[], object],
) -> None:
    current_count = require_count(get_count(), f"{name}.count")
    current_hash = require_sha256(
        get_content_hash(),
        f"{name}.content_hash",
    )
    if current_count != snapshot.count or not hmac.compare_digest(
        current_hash,
        snapshot.content_hash,
    ):
        raise RuntimeError(f"{name} changed during snapshot")


__all__ = [
    "StableCollectionSnapshot",
    "assert_stable_collection_snapshot",
    "require_count",
    "require_sha256",
    "require_text",
    "take_stable_collection_snapshot",
]
