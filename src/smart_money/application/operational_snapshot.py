from __future__ import annotations

import hmac
from dataclasses import dataclass
from typing import Protocol

from smart_money.core.ids import deterministic_id

_SCHEMA = "canonical_operational_snapshot.v1"


class _Collection(Protocol):
    @property
    def content_hash(self) -> str: ...


@dataclass(frozen=True, slots=True)
class CanonicalOperationalSnapshot:
    snapshot_id: str
    ledger_content_hash: str
    ledger_entry_count: int
    checkpoint_id: str | None
    commit_receipt_store_hash: str
    commit_receipt_count: int
    historical_manifest_store_hash: str
    historical_manifest_count: int
    historical_anchor_id: str
    run_store_hash: str
    run_count: int
    durable_audit_store_hash: str
    durable_audit_count: int
    durable_audit_anchor_id: str
    schema_version: str = _SCHEMA

    def identity_payload(self) -> dict[str, object]:
        return {
            field: getattr(self, field)
            for field in (
                "checkpoint_id",
                "commit_receipt_count",
                "commit_receipt_store_hash",
                "durable_audit_anchor_id",
                "durable_audit_count",
                "durable_audit_store_hash",
                "historical_anchor_id",
                "historical_manifest_count",
                "historical_manifest_store_hash",
                "ledger_content_hash",
                "ledger_entry_count",
                "run_count",
                "run_store_hash",
                "schema_version",
            )
        }

    def canonical_dict(self) -> dict[str, object]:
        return {"snapshot_id": self.snapshot_id, **self.identity_payload()}

    def __post_init__(self) -> None:
        if self.snapshot_id != deterministic_id(
            "canonical_operational_snapshot",
            self.identity_payload(),
        ):
            raise ValueError("snapshot_id does not match deterministic payload")


def make_canonical_operational_snapshot(
    *,
    ledger: _Collection,
    ledger_entry_count: int,
    checkpoint_id: str | None,
    commit_store: _Collection,
    commit_receipt_count: int,
    historical_store: _Collection,
    historical_manifest_count: int,
    historical_anchor_id: str,
    run_store: _Collection,
    run_count: int,
    durable_audit_store: _Collection,
    durable_audit_count: int,
    durable_audit_anchor_id: str,
) -> CanonicalOperationalSnapshot:
    initial = (
        ledger.content_hash,
        commit_store.content_hash,
        historical_store.content_hash,
        run_store.content_hash,
        durable_audit_store.content_hash,
    )
    payload = {
        "checkpoint_id": checkpoint_id,
        "commit_receipt_count": commit_receipt_count,
        "commit_receipt_store_hash": initial[1],
        "durable_audit_anchor_id": durable_audit_anchor_id,
        "durable_audit_count": durable_audit_count,
        "durable_audit_store_hash": initial[4],
        "historical_anchor_id": historical_anchor_id,
        "historical_manifest_count": historical_manifest_count,
        "historical_manifest_store_hash": initial[2],
        "ledger_content_hash": initial[0],
        "ledger_entry_count": ledger_entry_count,
        "run_count": run_count,
        "run_store_hash": initial[3],
        "schema_version": _SCHEMA,
    }
    final = (
        ledger.content_hash,
        commit_store.content_hash,
        historical_store.content_hash,
        run_store.content_hash,
        durable_audit_store.content_hash,
    )
    if any(
        not hmac.compare_digest(before, after)
        for before, after in zip(initial, final, strict=True)
    ):
        raise RuntimeError("operational stores changed during snapshot")
    return CanonicalOperationalSnapshot(
        snapshot_id=deterministic_id(
            "canonical_operational_snapshot",
            payload,
        ),
        **payload,
    )


__all__ = [
    "CanonicalOperationalSnapshot",
    "make_canonical_operational_snapshot",
]
