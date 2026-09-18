from __future__ import annotations

from typing import Any

from smart_money.adapters.persistence.generic_collection_store import (
    GenericCollectionStore,
    StoreManifest,
)
from smart_money.application.early_entry_consistency_replay_verifier import (
    EarlyEntryConsistencyReplayReceipt,
)

_SCHEMA_VERSION = "early_entry_consistency_replay_store.v1"


def _parse(data: dict[str, Any]) -> EarlyEntryConsistencyReplayReceipt:
    return EarlyEntryConsistencyReplayReceipt(
        consistency_id=data["consistency_id"],
        matches=data["matches"],
        replay_id=data["replay_id"],
        schema_version=data.get("schema_version", _SCHEMA_VERSION),
    )


_MANIFEST = StoreManifest(
    schema_version=_SCHEMA_VERSION,
    collection_key="receipts",
    id_field="replay_id",
    parse=_parse,
    verify_canonical=True,
    document_keys=frozenset({"schema_version", "content_hash", "receipts"}),
)


class JsonEarlyEntryConsistencyReplayStore:
    def __init__(self, file_path: str | Any) -> None:
        self._inner = GenericCollectionStore(file_path, _MANIFEST)

    def append(self, receipt: EarlyEntryConsistencyReplayReceipt) -> str:
        return self._inner.append(receipt)

    def get(self, replay_id: str) -> EarlyEntryConsistencyReplayReceipt | None:
        return self._inner.get(replay_id)

    def iter_receipts(self):  # type: ignore[override]
        return self._inner.iter_items()

    @property
    def receipt_count(self) -> int:
        return self._inner.count


__all__ = ["JsonEarlyEntryConsistencyReplayStore"]
