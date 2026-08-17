from dataclasses import FrozenInstanceError

import pytest

from smart_money.application.operational_snapshot import (
    make_canonical_operational_snapshot,
)


class _Store:
    def __init__(self, marker: str) -> None:
        self.content_hash = marker * 64


def test_snapshot_is_deterministic_immutable_and_complete() -> None:
    stores = [_Store(value) for value in "abcde"]
    kwargs = {
        "ledger": stores[0],
        "ledger_entry_count": 3,
        "checkpoint_id": "checkpoint-a",
        "commit_store": stores[1],
        "commit_receipt_count": 2,
        "historical_store": stores[2],
        "historical_manifest_count": 1,
        "historical_anchor_id": "historical-head",
        "run_store": stores[3],
        "run_count": 2,
        "durable_audit_store": stores[4],
        "durable_audit_count": 1,
        "durable_audit_anchor_id": "durable-head",
    }
    first = make_canonical_operational_snapshot(**kwargs)
    second = make_canonical_operational_snapshot(**kwargs)
    assert first == second
    assert first.canonical_dict()["ledger_entry_count"] == 3
    assert not hasattr(first, "__dict__")
    with pytest.raises(FrozenInstanceError):
        first.run_count = 4  # type: ignore[misc]


def test_snapshot_fails_when_store_changes_during_read() -> None:
    class _Changing:
        reads = 0

        @property
        def content_hash(self):
            self.reads += 1
            return ("a" if self.reads == 1 else "b") * 64

    stable = _Store("c")
    with pytest.raises(RuntimeError, match="changed"):
        make_canonical_operational_snapshot(
            ledger=_Changing(),
            ledger_entry_count=0,
            checkpoint_id=None,
            commit_store=stable,
            commit_receipt_count=0,
            historical_store=stable,
            historical_manifest_count=0,
            historical_anchor_id="h",
            run_store=stable,
            run_count=0,
            durable_audit_store=stable,
            durable_audit_count=0,
            durable_audit_anchor_id="d",
        )
