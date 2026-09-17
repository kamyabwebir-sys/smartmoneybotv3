from __future__ import annotations

from typing import Any

from smart_money.adapters.persistence.generic_value_store import (
    GenericValueStore,
    ValueStoreManifest,
)
from smart_money.application.dashboard_session_recovery_gate import (
    DashboardSessionRecoveryReceipt,
)

_SCHEMA_VERSION = "dashboard_session_recovery_receipt_store.v1"


def _parse(data: dict[str, Any]) -> DashboardSessionRecoveryReceipt:
    return DashboardSessionRecoveryReceipt(**data)


_MANIFEST = ValueStoreManifest(
    schema_version=_SCHEMA_VERSION,
    value_key="receipt",
    id_field="receipt_id",
    parse=_parse,
    verify_canonical=True,
    content_hash=True,
    immutable=True,
    collision_message="session recovery rollback or overwrite rejected",
)


class JsonDashboardSessionRecoveryReceiptStore:
    """Atomic persistence for the latest session-chain recovery receipt."""

    def __init__(self, file_path: str | Any) -> None:
        self._inner = GenericValueStore(file_path, _MANIFEST)

    def save(self, receipt: DashboardSessionRecoveryReceipt) -> str:
        if not isinstance(receipt, DashboardSessionRecoveryReceipt):
            raise TypeError("receipt must be a DashboardSessionRecoveryReceipt")
        return self._inner.save(receipt)

    def load(self) -> DashboardSessionRecoveryReceipt | None:
        return self._inner.load()


__all__ = ["JsonDashboardSessionRecoveryReceiptStore"]
