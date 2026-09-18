from __future__ import annotations

from typing import Any

from smart_money.adapters.persistence.generic_collection_store import (
    GenericCollectionStore,
    StoreManifest,
)
from smart_money.application.dashboard_recovery_replay_verifier import (
    DashboardRecoveryReplayReceipt,
)

_SCHEMA_VERSION = "dashboard_recovery_replay_store.v1"


def _parse(data: dict[str, Any]) -> DashboardRecoveryReplayReceipt:
    return DashboardRecoveryReplayReceipt(
        expected_receipt_id=data["expected_receipt_id"],
        actual_receipt_id=data["actual_receipt_id"],
        matches=data["matches"],
        mismatches=tuple(data.get("mismatches", ())),
        schema_version=data.get("schema_version", "dashboard_recovery_replay.v1"),
    )


_MANIFEST = StoreManifest(
    schema_version=_SCHEMA_VERSION,
    collection_key="receipts",
    id_field="verification_id",  # @property on the receipt
    parse=_parse,
    verify_canonical=True,
    document_keys=frozenset({"schema_version", "content_hash", "receipts"}),
)


class JsonDashboardRecoveryReplayStore:
    """Atomic, append-only persistence for recovery replay receipts."""

    def __init__(self, file_path: str | Any) -> None:
        self._inner = GenericCollectionStore(file_path, _MANIFEST)

    def append(self, receipt: DashboardRecoveryReplayReceipt) -> str:
        return self._inner.append(receipt)

    def get(self, verification_id: str) -> DashboardRecoveryReplayReceipt | None:
        return self._inner.get(verification_id)

    def iter_receipts(self):  # type: ignore[override]
        return self._inner.iter_items()

    @property
    def receipt_count(self) -> int:
        return self._inner.count

    @property
    def content_hash(self) -> str:
        return self._inner.content_hash


__all__ = ["JsonDashboardRecoveryReplayStore"]
