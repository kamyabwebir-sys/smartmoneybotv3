import json

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
