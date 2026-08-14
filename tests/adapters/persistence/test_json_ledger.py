import json

import pytest

from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.ingestion.contracts import EvidencePayload


def test_ledger_round_trip_persistence(tmp_path):
    # Setup
    ledger = EvidenceGroundingLedger()
    payload = EvidencePayload("SRC-1", "market_structure", 123456, {"price": 100})
    ledger.record(payload)

    # Save
    file_path = tmp_path / "ledger.json"
    ledger.save_to_disk(file_path)

    # Load into new instance
    new_ledger = EvidenceGroundingLedger()
    new_ledger.load_from_disk(file_path)

    # Verify
    assert new_ledger.count == 1
    loaded_entry = list(new_ledger.get_all_entries())[0]
    assert loaded_entry.payload.source_id == "SRC-1"
    assert loaded_entry.canonical_id == payload.get_canonical_id()
    assert loaded_entry.payload.data["price"] == 100


def test_ledger_v2_round_trip_is_byte_stable_and_content_addressed(tmp_path):
    ledger = EvidenceGroundingLedger()
    ledger.record(EvidencePayload("SRC-1", "market_structure", 100, {"price": 10}))
    ledger.record(EvidencePayload("SRC-2", "market_structure", 101, {"price": 20}))

    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    ledger.save_to_disk(first_path)
    first_bytes = first_path.read_bytes()
    document = json.loads(first_bytes)

    assert document["schema_version"] == "evidence_ledger.v2"
    assert document["content_hash"] == ledger.content_hash
    assert len(document["content_hash"]) == 64

    restored = EvidenceGroundingLedger()
    restored.load_from_disk(first_path)
    restored.save_to_disk(second_path)

    assert second_path.read_bytes() == first_bytes
    assert restored.content_hash == ledger.content_hash
    assert tuple(restored.iter_payloads()) == tuple(ledger.iter_payloads())


def test_v1_ledger_is_loaded_and_rewritten_as_v2(tmp_path):
    payload = EvidencePayload("SRC-1", "market_structure", 100, {"price": 10})
    file_path = tmp_path / "legacy-v1.json"
    file_path.write_text(
        json.dumps(
            {
                "schema_version": "evidence_ledger.v1",
                "entries": [
                    {
                        "canonical_id": payload.get_canonical_id(),
                        "payload": payload.canonical_dict(),
                    }
                ],
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    ledger = EvidenceGroundingLedger()
    ledger.load_from_disk(file_path)
    ledger.save_to_disk(file_path)

    migrated = json.loads(file_path.read_text(encoding="utf-8"))
    assert migrated["schema_version"] == "evidence_ledger.v2"
    assert migrated["content_hash"] == ledger.content_hash


def test_unknown_schema_version_fails_closed(tmp_path):
    file_path = tmp_path / "unknown-schema.json"
    file_path.write_text(
        json.dumps({"schema_version": "evidence_ledger.v99", "entries": []}),
        encoding="utf-8",
    )

    ledger = EvidenceGroundingLedger()
    with pytest.raises(ValueError, match="unsupported ledger schema_version"):
        ledger.load_from_disk(file_path)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda document: document.pop("content_hash"), "document keys"),
        (lambda document: document.update({"extra": True}), "document keys"),
        (
            lambda document: document.update({"content_hash": "not-a-hash"}),
            "lowercase SHA-256",
        ),
        (
            lambda document: document["entries"][0].update({"extra": True}),
            "entry keys",
        ),
        (
            lambda document: document["entries"][0]["payload"].pop("metadata"),
            "payload keys",
        ),
    ],
    ids=[
        "missing-content-hash",
        "extra-document-key",
        "malformed-content-hash",
        "extra-entry-key",
        "missing-payload-key",
    ],
)
def test_v2_schema_shape_is_strict(tmp_path, mutation, message):
    ledger = EvidenceGroundingLedger()
    ledger.record(EvidencePayload("SRC-1", "market_structure", 100, {"price": 10}))
    file_path = tmp_path / "strict-schema.json"
    ledger.save_to_disk(file_path)
    document = json.loads(file_path.read_text(encoding="utf-8"))
    mutation(document)
    file_path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        EvidenceGroundingLedger().load_from_disk(file_path)


def test_content_tampering_is_detected_without_replacing_existing_state(tmp_path):
    persisted = EvidenceGroundingLedger()
    persisted.record(
        EvidencePayload("SRC-1", "market_structure", 100, {"price": 10})
    )
    file_path = tmp_path / "tampered.json"
    persisted.save_to_disk(file_path)

    document = json.loads(file_path.read_text(encoding="utf-8"))
    document["entries"][0]["payload"]["data"]["price"] = 999
    file_path.write_text(json.dumps(document), encoding="utf-8")

    active = EvidenceGroundingLedger()
    retained = EvidencePayload("ACTIVE", "market_structure", 200, {"price": 20})
    active.record(retained)

    with pytest.raises(ValueError, match="content hash mismatch"):
        active.load_from_disk(file_path)

    assert active.entry_count == 1
    assert active.get(retained.get_canonical_id()) == retained


def test_duplicate_and_identity_mismatch_are_rejected(tmp_path):
    ledger = EvidenceGroundingLedger()
    payload = EvidencePayload("SRC-1", "market_structure", 100, {"price": 10})
    ledger.record(payload)
    file_path = tmp_path / "invalid-identities.json"
    ledger.save_to_disk(file_path)
    document = json.loads(file_path.read_text(encoding="utf-8"))

    duplicate_document = {
        **document,
        "entries": [document["entries"][0], document["entries"][0]],
    }
    duplicate_entries = duplicate_document["entries"]
    duplicate_document["content_hash"] = ledger._compute_content_hash(
        duplicate_entries
    )
    file_path.write_text(json.dumps(duplicate_document), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate canonical_id"):
        EvidenceGroundingLedger().load_from_disk(file_path)

    mismatch_document = document
    mismatch_document["entries"][0]["canonical_id"] = "wrong-id"
    mismatch_document["content_hash"] = ledger._compute_content_hash(
        mismatch_document["entries"]
    )
    file_path.write_text(json.dumps(mismatch_document), encoding="utf-8")
    with pytest.raises(ValueError, match="identity mismatch"):
        EvidenceGroundingLedger().load_from_disk(file_path)
