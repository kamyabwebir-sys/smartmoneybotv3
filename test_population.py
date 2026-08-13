from contracts import EvidencePayload
from ledger import EvidenceGroundingLedger
from population import EvidencePopulator


def test_full_flow_ingest_to_population():
    ledger = EvidenceGroundingLedger()
    populator = EvidencePopulator()

    # Simulate an entry in ledger
    payload = EvidencePayload("S1", "market_structure", 100, {"trend": "bullish"})
    ledger.record(payload)

    # Process from ledger to domain
    entries = list(ledger.get_unprocessed_entries())
    assert len(entries) == 1

    domain_obj = populator.populate(entries[0])
    assert domain_obj["id"] == entries[0].canonical_id
    assert domain_obj["raw_data"]["trend"] == "bullish"
