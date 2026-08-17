from __future__ import annotations

import json

import pytest

from smart_money.adapters.persistence.commit_receipt_store import (
    JsonCommitReceiptStore,
)
from smart_money.application.durable_ingestion_commit import (
    DurableIngestionCommitReceipt,
)
from smart_money.application.ports.commit_receipt_store import (
    CommitReceiptStore,
)
from smart_money.core.ids import deterministic_id


def _receipt(marker: str) -> DurableIngestionCommitReceipt:
    payload: dict[str, str | int] = {
        "accepted_count": 1,
        "checkpoint_id": f"checkpoint-{marker}",
        "event_id": f"event-{marker}",
        "evidence_id": f"evidence-{marker}",
        "ledger_content_hash": marker * 64,
        "market_id": f"market-{marker}",
        "provider_id": f"provider-{marker}",
        "schema_version": "durable_ingestion_commit.v1",
        "session_id": f"session-{marker}",
        "source_event_id": f"source-event-{marker}",
    }
    return DurableIngestionCommitReceipt(
        receipt_id=deterministic_id("durable_ingestion_commit", payload),
        session_id=payload["session_id"],
        provider_id=payload["provider_id"],
        market_id=payload["market_id"],
        event_id=payload["event_id"],
        source_event_id=payload["source_event_id"],
        evidence_id=payload["evidence_id"],
        ledger_content_hash=payload["ledger_content_hash"],
        checkpoint_id=payload["checkpoint_id"],
        accepted_count=1,
    )


def test_store_is_append_only_byte_stable_and_satisfies_port(tmp_path) -> None:
    path = tmp_path / "commits.json"
    store = JsonCommitReceiptStore(path)
    first = _receipt("a")
    second = _receipt("b")

    first_id = store.append(first)
    first_bytes = path.read_bytes()
    duplicate_id = store.append(first)

    assert isinstance(store, CommitReceiptStore)
    assert first_id == duplicate_id == first.receipt_id
    assert path.read_bytes() == first_bytes
    assert store.receipt_count == 1

    store.append(second)
    restored = JsonCommitReceiptStore(path)
    document = json.loads(path.read_text(encoding="utf-8"))

    assert tuple(restored.iter_receipts()) == (first, second)
    assert restored.get(first.receipt_id) == first
    assert restored.get("missing") is None
    assert restored.receipt_count == 2
    assert restored.content_hash == document["content_hash"]
    assert document["schema_version"] == "durable_ingestion_commit_store.v1"


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda document: document.pop("content_hash"), "document keys"),
        (lambda document: document.update({"extra": True}), "document keys"),
        (
            lambda document: document.update({"schema_version": "store.v99"}),
            "unsupported",
        ),
        (
            lambda document: document.update({"content_hash": "NOT-A-HASH"}),
            "lowercase SHA-256",
        ),
        (
            lambda document: document.update({"receipts": {}}),
            "must be a list",
        ),
        (
            lambda document: document["receipts"][0].update({"extra": True}),
            "receipt keys",
        ),
    ],
)
def test_store_schema_is_strict(tmp_path, mutation, message) -> None:
    path = tmp_path / "strict.json"
    JsonCommitReceiptStore(path).append(_receipt("a"))
    document = json.loads(path.read_text(encoding="utf-8"))
    mutation(document)
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        JsonCommitReceiptStore(path)


def test_receipt_tampering_is_detected_by_collection_hash(tmp_path) -> None:
    path = tmp_path / "tampered.json"
    JsonCommitReceiptStore(path).append(_receipt("a"))
    document = json.loads(path.read_text(encoding="utf-8"))
    document["receipts"][0]["event_id"] = "tampered"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        JsonCommitReceiptStore(path)


def test_forged_receipt_is_rejected_with_recomputed_hash(tmp_path) -> None:
    path = tmp_path / "forged.json"
    store = JsonCommitReceiptStore(path)
    store.append(_receipt("a"))
    document = json.loads(path.read_text(encoding="utf-8"))
    document["receipts"][0]["event_id"] = "forged"
    document["content_hash"] = store._compute_content_hash(
        document["receipts"]
    )
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="invalid durable"):
        JsonCommitReceiptStore(path)


def test_duplicate_identity_in_file_is_rejected(tmp_path) -> None:
    path = tmp_path / "duplicate.json"
    store = JsonCommitReceiptStore(path)
    store.append(_receipt("a"))
    document = json.loads(path.read_text(encoding="utf-8"))
    document["receipts"].append(document["receipts"][0])
    document["content_hash"] = store._compute_content_hash(
        document["receipts"]
    )
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate commit receipt"):
        JsonCommitReceiptStore(path)


def test_valid_orphaned_temporary_store_is_recovered(tmp_path) -> None:
    path = tmp_path / "recoverable.json"
    temporary_path = tmp_path / "recoverable.json.tmp"
    receipt = _receipt("a")
    JsonCommitReceiptStore(path).append(receipt)
    path.replace(temporary_path)

    restored = JsonCommitReceiptStore(path)

    assert restored.get(receipt.receipt_id) == receipt
    assert path.is_file()
    assert not temporary_path.exists()


def test_invalid_orphaned_temporary_store_is_retained(tmp_path) -> None:
    path = tmp_path / "invalid.json"
    temporary_path = tmp_path / "invalid.json.tmp"
    temporary_path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(ValueError, match="temporary commit receipt recovery"):
        JsonCommitReceiptStore(path)

    assert not path.exists()
    assert temporary_path.is_file()


def test_primary_store_remains_authoritative(tmp_path) -> None:
    path = tmp_path / "authoritative.json"
    temporary_path = tmp_path / "authoritative.json.tmp"
    primary = _receipt("a")
    JsonCommitReceiptStore(path).append(primary)
    primary_bytes = path.read_bytes()
    temporary_path.write_text("{not-json", encoding="utf-8")

    restored = JsonCommitReceiptStore(path)

    assert tuple(restored.iter_receipts()) == (primary,)
    assert path.read_bytes() == primary_bytes
    assert temporary_path.is_file()


def test_failed_append_does_not_mutate_in_memory_state(tmp_path) -> None:
    blocked_parent = tmp_path / "not-a-directory"
    blocked_parent.write_text("blocked", encoding="utf-8")
    store = JsonCommitReceiptStore(blocked_parent / "commits.json")

    with pytest.raises(OSError):
        store.append(_receipt("a"))

    assert store.receipt_count == 0
