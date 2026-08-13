import os

from contracts import EvidencePayload
from ledger import EvidenceGroundingLedger


def test_ledger_round_trip_persistence(tmp_path):
    # Setup
    ledger = EvidenceGroundingLedger()
    payload = EvidencePayload("SRC-1", "market_structure", 123456, {"price": 100})
    ledger.record(payload)

    # Save
    file_path = os.path.join(tmp_path, "ledger.json")
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
